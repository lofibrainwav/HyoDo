# Trinity Score: 93.0 (Discord Integration Service)
"""
AFO Kingdom Discord Bot Service
통합 대변인 시스템의 디스코드 채널 연동 모듈

Author: AFO Kingdom Development Team
Date: 2026-01-16
"""

import asyncio
import logging
import os

logger = logging.getLogger(__name__)

# Discord.py는 별도 설치 필요: pip install discord.py
try:
    import discord
    from discord.ext import commands

    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logger.warning("discord.py not installed. Run: pip install discord.py")


class AFODiscordBot:
    """
    AFO Kingdom 디스코드 봇.
    통합 메시징 서비스와 연결하여 카카오톡과 동일한 경험 제공.
    """

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("DISCORD_BOT_TOKEN")
        self.bot: commands.Bot | None = None
        self.api_base_url = os.getenv("AFO_API_URL", "http://localhost:8010")

        if DISCORD_AVAILABLE and self.token:
            intents = discord.Intents.default()
            intents.message_content = True
            self.bot = commands.Bot(command_prefix="!", intents=intents)
            self._setup_events()
            self._setup_commands()

    def _setup_events(self) -> None:
        """Discord 이벤트 핸들러 설정"""

        @self.bot.event
        async def on_ready():
            logger.info(f"✅ AFO Kingdom Discord Bot 연결됨: {self.bot.user}")
            logger.info(f"   - 서버 수: {len(self.bot.guilds)}")

        @self.bot.event
        async def on_message(message: discord.Message):
            # 봇 자신의 메시지는 무시
            if message.author == self.bot.user:
                return

            # "승상" 또는 "AFO" 멘션 시 응답
            if "승상" in message.content or "AFO" in message.content.upper():
                await self._handle_afo_message(message)

            # 명령어 처리
            await self.bot.process_commands(message)

    def _setup_commands(self) -> None:
        """Discord 슬래시 명령어 설정"""

        @self.bot.command(name="상태")
        async def status_command(ctx: commands.Context):
            """왕국 상태 확인"""
            response = await self._call_afo_api("/상태", ctx.author.name)
            await ctx.send(response)

        @self.bot.command(name="도움")
        async def help_command(ctx: commands.Context):
            """도움말 표시"""
            embed = discord.Embed(
                title="👑 AFO Kingdom 봇 도움말",
                description="사령관님을 위한 왕국 대변인 시스템",
                color=discord.Color.gold(),
            )
            embed.add_field(name="!상태", value="왕국 시스템 상태 확인", inline=False)
            embed.add_field(name="!도움", value="이 도움말 표시", inline=False)
            embed.add_field(name="승상, [질문]", value="승상에게 직접 질문", inline=False)
            await ctx.send(embed=embed)

    async def _handle_afo_message(self, message: discord.Message) -> None:
        """AFO 관련 메시지 처리"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            payload = {
                "msg": message.content,
                "sender": str(message.author),
                "channel": "discord",
                "guild": str(message.guild.name) if message.guild else "DM",
            }

            try:
                async with session.post(
                    f"{self.api_base_url}/api/discord/webhook", json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        reply = data.get("reply", "응답을 생성할 수 없습니다.")

                        # Discord 형식으로 변환
                        discord_reply = reply.replace("[AFO 승상]", "**[AFO Kingdom Spokesman]**")

                        embed = discord.Embed(description=discord_reply, color=discord.Color.blue())
                        embed.set_footer(text=f"Engine: {data.get('engine', 'Unknown')}")
                        await message.reply(embed=embed)
                    else:
                        await message.reply("❌ 왕국과의 연결에 문제가 발생했습니다.")
            except Exception as e:
                logger.error(f"Discord API 호출 실패: {e}")
                await message.reply("⚠️ 일시적인 오류가 발생했습니다.")

    async def _call_afo_api(self, command: str, sender: str) -> str:
        """AFO API 호출"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            payload = {"msg": command, "sender": sender, "channel": "discord"}
            async with session.post(
                f"{self.api_base_url}/api/discord/webhook", json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("reply", "응답 없음")
                return "❌ API 호출 실패"

    async def start(self) -> None:
        """봇 시작"""
        if not DISCORD_AVAILABLE:
            logger.error("discord.py가 설치되지 않았습니다.")
            return

        if not self.token:
            logger.error("DISCORD_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
            return

        logger.info("🚀 AFO Kingdom Discord Bot 시작 중...")
        await self.bot.start(self.token)

    def run(self) -> None:
        """동기 실행"""
        asyncio.run(self.start())


# 싱글톤 인스턴스
discord_bot = AFODiscordBot()


# CLI 엔트리포인트
if __name__ == "__main__":
    import sys

    if not DISCORD_AVAILABLE:
        print("❌ discord.py가 필요합니다: pip install discord.py aiohttp")
        sys.exit(1)

    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ DISCORD_BOT_TOKEN 환경변수를 설정하세요.")
        print("   export DISCORD_BOT_TOKEN='your-bot-token'")
        sys.exit(1)

    bot = AFODiscordBot(token)
    bot.run()
