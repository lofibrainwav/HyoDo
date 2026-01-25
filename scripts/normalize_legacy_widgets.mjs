#!/usr/bin/env node
/**
 * HTML 위젯 규격 표준화 스크립트
 * 
 * kingdom_dashboard.html의 섹션에 data-widget-id를 자동 주입
 * 
 * 사용법:
 *   node scripts/normalize_legacy_widgets.mjs
 * 
 * 백업: 원본 파일은 .bak으로 저장됨
 */

import { readFileSync, writeFileSync, copyFileSync } from 'fs';
import { join } from 'path';

const HTML_FILE = join(process.cwd(), 'packages/dashboard/public/legacy/kingdom_dashboard.html');
const BACKUP_FILE = `${HTML_FILE}.bak`;

// 핵심 섹션 매핑 (섹션 ID → 위젯 ID)
const SECTION_WIDGET_MAP = {
  'philosophy': 'philosophy-widget',
  'realtime-status': 'realtime-status-widget',
  'architecture': 'architecture-widget',
  'chancellor': 'chancellor-widget',
  'architecture-detail': 'architecture-detail-widget',
  'organs-map': 'organs-map-widget',
  'ssot': 'ssot-widget',
  'lock': 'lock-widget',
  'organs': 'organs-widget',
  'integrity': 'integrity-widget',
  'table-of-contents': 'table-of-contents-widget',
  'git-tree-analysis': 'git-tree-widget',
  'project-structure': 'project-structure-widget',
  'mcp-tools': 'mcp-tools-widget',
  'tools': 'tools-widget',
};

function normalizeWidgets() {
  console.log('📐 HTML 위젯 규격 표준화 시작...\n');

  // 백업 생성
  console.log('1. 백업 생성...');
  copyFileSync(HTML_FILE, BACKUP_FILE);
  console.log(`   ✅ 백업 완료: ${BACKUP_FILE}\n`);

  // HTML 읽기
  console.log('2. HTML 파일 읽기...');
  let html = readFileSync(HTML_FILE, 'utf-8');
  console.log(`   ✅ 파일 크기: ${html.length} bytes\n`);

  // 섹션에 data-widget-id 주입
  console.log('3. 섹션에 data-widget-id 주입...');
  let modified = 0;

  for (const [sectionId, widgetId] of Object.entries(SECTION_WIDGET_MAP)) {
    // 패턴: <section id="section-id" ...>
    const pattern = new RegExp(
      `(<section\\s+id=["']${sectionId}["'][^>]*?)(\\s+data-widget-id=["'][^"']*["'])?(\\s+class=["'][^"']*["'])?(>)`,
      'i'
    );

    if (pattern.test(html)) {
      // 이미 data-widget-id가 있으면 업데이트, 없으면 추가
      const replacement = (match, p1, p2, p3, p4) => {
        if (p2) {
          // 이미 있으면 업데이트
          return `${p1} data-widget-id="${widgetId}"${p3 || ''}${p4}`;
        } else {
          // 없으면 추가
          return `${p1} data-widget-id="${widgetId}"${p3 || ''}${p4}`;
        }
      };

      const before = html;
      html = html.replace(pattern, replacement);
      
      if (before !== html) {
        modified++;
        console.log(`   ✅ ${sectionId} → ${widgetId}`);
      }
    } else {
      console.log(`   ⚠️  섹션 "${sectionId}"를 찾을 수 없음`);
    }
  }

  console.log(`\n   총 ${modified}개 섹션 수정됨\n`);

  // 수정된 HTML 저장
  if (modified > 0) {
    console.log('4. 수정된 HTML 저장...');
    writeFileSync(HTML_FILE, html, 'utf-8');
    console.log(`   ✅ 저장 완료: ${HTML_FILE}\n`);
  } else {
    console.log('4. 변경사항 없음 (이미 표준화됨)\n');
  }

  // 검증: data-widget-id 개수 확인
  console.log('5. 검증...');
  const widgetIdMatches = html.match(/data-widget-id=["'][^"']*["']/g);
  const widgetIdCount = widgetIdMatches ? widgetIdMatches.length : 0;
  console.log(`   ✅ data-widget-id 속성: ${widgetIdCount}개\n`);

  console.log('✅ 위젯 규격 표준화 완료!\n');
  console.log('다음 단계:');
  console.log('  1. HTML 파일 확인: packages/dashboard/public/legacy/kingdom_dashboard.html');
  console.log('  2. 빌드 검증: pnpm -C packages/dashboard build');
  console.log('  3. 롤백 (필요시): cp packages/dashboard/public/legacy/kingdom_dashboard.html.bak packages/dashboard/public/legacy/kingdom_dashboard.html');
}

try {
  normalizeWidgets();
} catch (error) {
  console.error('❌ 오류 발생:', error.message);
  process.exit(1);
}

