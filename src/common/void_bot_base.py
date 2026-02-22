# SC2 imports
from sc2.bot_ai import BotAI

# Base imports
from loguru import logger
from datetime import datetime
import os
import json

# Additional imports
import pandas as pd
from path import SC2_VOID_BOT_HOME

class VoidBotBase(BotAI):

    # Each bot optionally overrides this
    async def custom_on_start(self):
        pass

    # Default on start, sets up logging
    async def on_start(self):

        if os.getenv("DEV"):
            # Setup log paths
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            map_name = self.game_info.map_name.replace(" ", "_")
            base_filename = f"{self.__class__.__name__}_{map_name}_{self.enemy_race}_{timestamp}"
            log_dir = os.path.join(SC2_VOID_BOT_HOME, "logs")
            os.makedirs(log_dir, exist_ok=True)
            self.pandas_csv_path = os.path.join(log_dir, base_filename + ".csv")

            # Get stat keys from score summary
            self.stat_keys = [stat[0] for stat in self.state.score.summary]

            # Create empty DataFrame with 'game_time' + stat keys
            self.df = pd.DataFrame(columns=["game_time"] + self.stat_keys)

        # Call the custom method
        await self.custom_on_start()

    # Default on step, calls custom on step
    async def on_step(self, iteration):
    
        if os.getenv("DEV"):
            # Current stats
            stats = {stat[0]: float(stat[1]) for stat in self.state.score.summary}
            row = {"game_time": self.time}
            row.update(stats)

            # Append row
            self.df.loc[len(self.df)] = row

        # Call custom on step
        await self.custom_on_step(iteration)

    # Custom on step, can be overridden by each bot
    async def custom_on_step(self, iteration):
        pass

    # Default on end fcn, mostly does logging
    async def on_end(self, game_result):

        if os.getenv("DEV"):
            # Save to CSV
            self.df.to_parquet(self.pandas_csv_path.replace(".csv", ".parquet"), index=False)

        # Get and specific bot logic
        await self.custom_on_end(game_result)

    # Each bot optionally overrides this
    async def custom_on_end(self, game_result):
        pass
