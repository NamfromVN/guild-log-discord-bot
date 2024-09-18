import asyncio
import os
import shutil
from typing import Optional

# import subprocess
import disnake
from disnake.ext import commands

from utils.ClientUser import ClientUser
from utils.error import GenericError


def format_git_log(data_list: list):

    data = []

    for d in data_list:
        if not d:
            continue
        t = d.split("*****")
        data.append({"commit": t[0], "abbreviated_commit": t[1], "subject": t[2], "timestamp": t[3]})

    return data

async def run_command(cmd: str):

    p = await asyncio.create_subprocess_shell(
        cmd, stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, stderr = await p.communicate()
    r = ShellResult(p.returncode, stdout, stderr)
    if r.status != 0:
        raise GenericError(f"{r.stderr or r.stdout}\n\nStatus Code: {r.status}")
    return str(r.stdout)



class ShellResult:

    def __init__(self, status: int, stdout: Optional[bytes], stderr: Optional[bytes]):
        self.status = status
        self.stdout = stdout.decode(encoding="utf-8", errors="replace") if stdout is not None else None
        self.stderr = stderr.decode(encoding="utf-8", errors="replace") if stderr is not None else None


class Owner(commands.Cog):

    os_quote = "\"" if os.name == "nt" else "'"
    git_format = f"--pretty=format:{os_quote}%H*****%h*****%s*****%ct{os_quote}"
    def __init__(self, bot: ClientUser):
        self.bot = bot
        self.git_init_cmds = [
            "git init",
            f'git remote add origin {os.environ.get("SOURCE_REPO")}',
            'git fetch origin',
            'git checkout -b main -f --track origin/main'
        ]
        
    async def reload_module(self):
    
        self.bot.load_modules()
        

    @commands.is_owner()
    @commands.command()
    async def restart(self, ctx: disnake.ApplicationCommandInteraction):
        await ctx.send("Đang khởi động lại...")
        await asyncio.sleep(5)
        await self.bot.close()
        try:
            os.system("python3 main.py")
        except:
            os.system("py main.py")

    @commands.is_owner()
    @commands.command()
    async def shutdown(self, ctx: disnake.ApplicationCommandInteraction):
        await ctx.send("GoodBye")
        await asyncio.sleep(5)
        await self.bot.close()


    @commands.is_owner()
    @commands.slash_command(name="reload", description="Tải lại các module")
    async def _reload_module(self, ctx: disnake.ApplicationCommandInteraction):
        await ctx.response.defer()
        await self.reload_module()
        await ctx.edit_original_response("Đã tải lại các module và event")

    def format_log(self, data: list):
        return "\n".join(f"[`{c['abbreviated_commit']}`]({self.bot.remote_git_url}/commit/{c['commit']}) `- "
                         f"{(c['subject'][:40].replace('`', '') + '...') if len(c['subject']) > 39 else c['subject']}` "
                         f"(<t:{c['timestamp']}:R>)" for c in data)
    @commands.is_owner()
    @commands.max_concurrency(1, commands.BucketType.default)
    @commands.slash_command(description="Cập nhật mã nguồn thông qua git")
    async def update(self, ctx: disnake.ApplicationCommandInteraction):
        out_git = ""

        git_log = []

        try:
            await ctx.response.defer()
        except:
            pass

        update_git = True
        rename_git_bak = False

        if update_git:

            if rename_git_bak or os.environ.get("HOSTNAME") == "squarecloud.app" and os.path.isdir("./.gitbak"):
                try:
                    shutil.rmtree("./.git")
                except:
                    pass
                os.rename("./.gitbak", "./.git")

            try:
                await run_command("git reset --hard")
            except:
                pass

            try:
                pull_log = await run_command("git pull --allow-unrelated-histories -X theirs")
                if "Already up to date" in pull_log:
                    raise GenericError("**Tôi đã cài đặt bản cập nhật mới nhất...**")
                out_git += pull_log

            except GenericError as e:
                raise e

            except Exception as e:

                if "Already up to date" in str(e):
                    raise GenericError("Tôi đã cài đặt các bản cập nhật mới nhất...")

                elif not "Fast-forward" in str(e):
                    out_git += await self.cleanup_git(force=True)

                elif "Need to specify how to reconcile divergent branches" in str(e):
                    out_git += await run_command("git rebase --no-ff")

            commit = ""

            for l in out_git.split("\n"):
                if l.startswith("Updating"):
                    commit = l.replace("Updating ", "").replace("..", "...")
                    break

            data = (await run_command(f"git log {commit} {self.git_format}")).split("\n")

            git_log += format_git_log(data)

        if os.environ.get("HOSTNAME") == "squarecloud.app":
            try:
                shutil.rmtree("./.gitbak")
            except:
                pass
            shutil.copytree("./.git", "./.gitbak")

        text = "`Tôi sẽ cần phải khởi động lại sau khi thay đổi.`"

        txt = f"`✅` **Cập nhật hoàn tất thành công!**"

        if git_log:
            txt += f"\n\n{self.format_log(git_log[:10])}"

        txt += f"\n\n`📄` **Log:** ```py\n{out_git[:1000].split('Fast-forward')[-1]}```\n{text}"

        if isinstance(ctx, disnake.ApplicationCommandInteraction):
            embed = disnake.Embed(
                description=txt
            )
            await ctx.send(embed=embed)
    async def cleanup_git(self, force=False):

        if force:
            try:
                shutil.rmtree("./.git")
            except FileNotFoundError:
                pass

        out_git = ""

        for c in self.git_init_cmds:
            try:
                out_git += (await run_command(c)) + "\n"
            except Exception as e:
                out_git += f"{e}\n"

        return out_git

def setup(bot: ClientUser):
    bot.add_cog(Owner(bot))