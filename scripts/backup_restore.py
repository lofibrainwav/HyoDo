#!/usr/bin/env python3
"""
AFO 왕국 백업 및 복구 스크립트
중요 데이터 및 설정의 안전한 백업/복구
"""

import json
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class BackupManager:
    def __init__(self, backup_dir: str = "backups") -> None:
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # 백업 대상 설정
        self.backup_targets = {
            "models": {
                "source": "~/.ollama/models",
                "description": "Ollama 모델 파일",
                "critical": True,
            },
            "database": {
                "source": "data",
                "description": "데이터베이스 파일",
                "critical": True,
            },
            "configs": {
                "source": "packages/afo-core/config",
                "description": "설정 파일",
                "critical": True,
            },
            "env_files": {
                "source": "*.env*",
                "description": "환경 변수 파일",
                "critical": True,
            },
            "logs": {"source": "logs", "description": "로그 파일", "critical": False},
            "artifacts": {
                "source": "artifacts",
                "description": "생성된 아티팩트",
                "critical": False,
            },
        }

    def create_backup(self, name: str = None, include_non_critical: bool = False) -> str:
        """백업 생성"""
        if name is None:
            name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = self.backup_dir / f"{name}.tar.gz"
        temp_dir = self.backup_dir / f"temp_{name}"
        temp_dir.mkdir(exist_ok=True)

        try:
            print(f"📦 백업 생성 시작: {name}")

            # 메타데이터 생성
            metadata = {
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "targets": {},
                "system_info": self._get_system_info(),
            }

            # 각 대상 백업
            for target_name, config in self.backup_targets.items():
                if not include_non_critical and not config["critical"]:
                    continue

                try:
                    source_path = Path(config["source"]).expanduser()
                    if source_path.exists():
                        # 대상 디렉토리 생성
                        target_dir = temp_dir / target_name
                        target_dir.mkdir(exist_ok=True)

                        if source_path.is_file():
                            shutil.copy2(source_path, target_dir / source_path.name)
                        else:
                            shutil.copytree(
                                source_path,
                                target_dir / source_path.name,
                                dirs_exist_ok=True,
                            )

                        metadata["targets"][target_name] = {
                            "status": "success",
                            "description": config["description"],
                            "size": self._get_dir_size(target_dir),
                        }

                        print(f"  ✅ {target_name}: {config['description']}")
                    else:
                        metadata["targets"][target_name] = {
                            "status": "skipped",
                            "reason": "source not found",
                        }
                        print(f"  ⚠️ {target_name}: 소스 없음")

                except Exception as e:
                    metadata["targets"][target_name] = {
                        "status": "error",
                        "error": str(e),
                    }
                    print(f"  ❌ {target_name}: 오류 - {e}")

            # 메타데이터 저장
            with open(temp_dir / "backup_metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 압축
            print("🗜️ 압축 중...")
            with tarfile.open(backup_path, "w:gz") as tar:
                for item in temp_dir.rglob("*"):
                    if item.is_file():
                        tar.add(item, arcname=item.relative_to(temp_dir))

            # 임시 디렉토리 정리
            shutil.rmtree(temp_dir)

            # 백업 정보 출력
            backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            print(f"📦 백업 크기: {backup_size:.1f}MB")
            print(f"📁 백업 위치: {backup_path}")

            return str(backup_path)

        except Exception as e:
            # 오류 발생 시 임시 디렉토리 정리
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise e

    def list_backups(self) -> List[Dict[str, Any]]:
        """사용 가능한 백업 목록"""
        backups = []

        for backup_file in self.backup_dir.glob("*.tar.gz"):
            try:
                # 백업 파일에서 메타데이터 추출 (간단한 방법)
                backup_info = {
                    "name": backup_file.stem,
                    "path": str(backup_file),
                    "size": backup_file.stat().st_size / (1024 * 1024),  # MB
                    "created": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                }
                backups.append(backup_info)
            except Exception:
                continue

        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def restore_backup(self, backup_name: str, target_dir: str = None) -> bool:
        """백업 복구"""
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"

        if not backup_path.exists():
            raise FileNotFoundError(f"백업 파일을 찾을 수 없습니다: {backup_path}")

        if target_dir is None:
            target_dir = f"restore_{backup_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        target_path = Path(target_dir)
        target_path.mkdir(exist_ok=True)

        try:
            print(f"📦 백업 복구 시작: {backup_name}")
            print(f"📁 복구 위치: {target_path}")

            # 압축 해제
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(target_path)

            # 메타데이터 확인
            metadata_file = target_path / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                print("📋 복구된 항목:")
                for target_name, info in metadata.get("targets", {}).items():
                    if info.get("status") == "success":
                        print(f"  ✅ {target_name}: {info.get('description', '')}")
                    else:
                        print(f"  ⚠️ {target_name}: {info.get('status', 'unknown')}")

            print("✅ 백업 복구 완료")
            return True

        except Exception as e:
            print(f"❌ 백업 복구 실패: {e}")
            # 복구 실패 시 생성된 디렉토리 정리
            if target_path.exists():
                shutil.rmtree(target_path)
            return False

    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """오래된 백업 정리"""
        import time

        cutoff_time = time.time() - (keep_days * 24 * 60 * 60)
        removed_count = 0

        for backup_file in self.backup_dir.glob("*.tar.gz"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                removed_count += 1
                print(f"🗑️ 오래된 백업 삭제: {backup_file.name}")

        return removed_count

    def _get_system_info(self) -> dict:
        """시스템 정보 수집"""
        try:
            import platform

            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
            }
        except:
            return {"error": "system info unavailable"}

    def _get_dir_size(self, path: Path) -> int:
        """디렉토리 크기 계산"""
        total_size = 0
        for item in path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
        return total_size


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="AFO 왕국 백업/복구 도구")
    parser.add_argument("action", choices=["backup", "restore", "list", "cleanup"])
    parser.add_argument("--name", help="백업 이름")
    parser.add_argument("--target", help="복구 대상 디렉토리")
    parser.add_argument(
        "--include-non-critical", action="store_true", help="중요하지 않은 파일도 포함"
    )
    parser.add_argument("--keep-days", type=int, default=30, help="보관할 백업 일수 (cleanup용)")

    args = parser.parse_args()

    manager = BackupManager()

    try:
        if args.action == "backup":
            backup_path = manager.create_backup(args.name, args.include_non_critical)
            print(f"✅ 백업 완료: {backup_path}")

        elif args.action == "restore":
            if not args.name:
                print("❌ 복구할 백업 이름을 지정하세요 (--name)")
                return

            success = manager.restore_backup(args.name, args.target)
            if success:
                print("✅ 복구 완료")
            else:
                print("❌ 복구 실패")

        elif args.action == "list":
            backups = manager.list_backups()
            if backups:
                print("📦 사용 가능한 백업:")
                for backup in backups:
                    size_mb = backup["size"]
                    print(f"  📁 {backup['name']} ({size_mb:.1f}MB) - {backup['created'][:19]}")
            else:
                print("📦 사용 가능한 백업 없음")

        elif args.action == "cleanup":
            removed = manager.cleanup_old_backups(args.keep_days)
            print(f"🗑️ {removed}개의 오래된 백업 삭제됨")

    except Exception as e:
        print(f"❌ 오류: {e}")


if __name__ == "__main__":
    main()
