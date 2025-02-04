# Configuration Guide

This guide explains how to configure various aspects of the Hamster Kombat Key Generator project, including environment variables and MongoDB setup.

## Environment Variables

Ensure you have a `.env` file in the root directory with the following content:

```plaintext
BOT_TOKEN=your-telegram-bot-token
DB_URL=your-mongodb-url
```

## Startup method

Because this project combines a generator and a bot together, you can customize the startup method.
To simplify the setup of the startup method, the `StartupMethods` enumeration was created:
```python
class StartupMethods(enum.Enum):
    KeygenAndBot = 0  # Run both the key generator and the Telegram bot
    OnlyKeygen = 1     # Run only the key generator
    OnlyBot = 2        # Run only the Telegram bot
``` 
The `STARTUP_METHOD` variable is responsible for the startup method
For example, if you want to run both the telegram bot and the generator together, then you need to register the following:
```python
STARTUP_METHOD = StartupMethods.KeygenAndBot
```
If you only want to run the bot, you need to specify the following value:
```python
STARTUP_METHOD = StartupMethods.OnlyBot
```
Finally, if you only want to run the generator, you need to specify the following value:
```python
STARTUP_METHOD = StartupMethods.OnlyKeygen
```

## Key generator Setup

Configuring the generator allows you to select games to generate, set up delays, as well as set proxy servers and more.

### `GAME_PROMO_CONFIGS`

This variable stores all data about current games and allows you to make correct requests. Brief description of the fields:
- `promoId` and `appToken` - They are used to identify games and gain access to key generation
- `eventsDelay` - sets the delay (in seconds) between repeated requests to receive the key. too low a value will result in a generation error.
- `attemptsNumber` - sets the number of attempts that will be made to obtain the key. Some games may require an increased value for these attempts. if there is a lack of them, the key will not be received

### `GamePromoTypes`
This is an enumeration that is important in the logic of the entire algorithm. It is thanks to him that games are separated in parallel streams and identified. It also makes it easy to set STARTUP_GAMES

### `STARTUP_GAMES`
This constant is used to set the list of games for which the generator will generate codes.
By default, the generator will create codes for each game from `GAME_PROMO_CONFIGS`:
```python
KEYGEN_GAMES = [g for g in GamePromoTypes]
```
But you can set any list of games here. The main condition is that each element must be an object of the `GamePromoTypes' type.
For example, this setting allows the generator to create codes for only 2 games: My Clone Army and Bike Ride 3D:
```python
KEYGEN_GAMES = [GamePromoTypes.MyCloneArmy, GamePromoTypes.BikeRide3D]
```
You can also set the generation for only 1 game:
```python
KEYGEN_GAMES = [GamePromoTypes.MyCloneArmy]
```

### `KEYGEN_THREAD_COUNT`
This value is responsible for the number of parallel "streams" for generating games. I.e., it means how many times generation will be started for each game from the list of `KEYGEN_GAMES`.
> **Warning:**
> Increasing this value may lead to API rate limit errors. We recommend increasing this value only if you generate keys for only a few or one game

### `GENERATE_INTERVAL`
This value is responsible for the delay in seconds between the end of key generation and the beginning of new generation


### Proxy Setup
Proxy configuration is described in detail in [Proxy Setup](proxy-setup)

## Bot Setup
Setting up the bot involves specifying default limits, required channel subscriptions, and more

### Setting up Key limits 
Setting limits can take place in 2 stages: 
1. Setting the default values (described here) 
2. Setting personal values for an individual user (described below in the **MongoDB Setup** section)

Setting the default values involves changing only 2 constants:
1. `DEFAULT_DAILY_GAME_KEYS_LIMIT` - key limit for 1 single game
2. `DEFAULT_USER_MULTIPLIER` - key limit multiplier for 1 individual game
> **Info**
> The key limit is calculation using this formula:
> ```python
> user.get("gkey_limit") or DEFAULT_DAILY_GAME_KEYS_LIMIT * user.get("gkey_multiplier") * DEFAULT_USER_MULTIPLIER
> ```

### Set up a subscription channel:
- In `SUBSCRIBE_REQUIRED_CHANNEL_ID` , you need to specify the ID of the channel that people will need to subscribe to in order to use the bot. You can set this value to `None` to cancel this requirement.
> **Warning:**
> If you specify a value other than `None` as the `SUBSCRIBE_REQUIRED_CHANNEL_ID`, you must invite the bot to the specified channel as an administrator. Otherwise, the subscription verification will always fail.
- In `SUBSCRIBE_REQUIRED_CHANNEL_INVITE_LINK` you need to specify a link to the channel you want to subscribe to. This value will be assigned to the url of the subscribe channel button.  

## MongoDB Setup

The MongoDB instance does not require manual setup. The script will automatically create the necessary database, collections, and documents.

### Database Structure

- **Collections:**
  - `users`: Stores user information.
  - `keys`: Stores game keys.

- **Document Structure:**

  **`keys` Collection:**
  ```json
  {
      "_id": "GameName",
      "keys": ["GAME_XXX_XXX_XXX", "GAME_YYY_YYY_YYY"]
  }
  ```

  **`users` Collection:**
  ```json
  {
      "_id": 0,
      "language": "language_code",
      "history": {
          "GameName": ["KEY_1", "KEY_2"]
      },
      "last_used_date": "dd.mm.yyyy",
      "gkey_limit": 0,
      "gkey_multiplier": 0
  }
  ```
  
### Field Description

**`keys` Collection**

- `_id` - a unique value. takes the value of the game name based on `config.GamePromoTypes`
- `keys` - a list of the key pool for a specific game. It is a list of code strings for the game

**`users` Collection**

- `_id` - a unique value. takes the value of the telegram user ID
- `language` - optional value. takes the value of the language code based on those listed in `locales`. It is automatically installed after the user selects the language. If absent, it takes the value `config.DEFAULT_LANGUAGE`
- `history` - It contains several objects (let's call them `historyObject`). stores the history of all keys received for the current day to calculate the remaining limit and access the history for the user.
- `historyObject` - An object containing the name of the game as a key, and as a value a list of keys received today in the same format as `keys` from the keys collection
- `last_used_date` - it contains a timestamp in the format `%d.%m.%Y`. It is automatically updated every day and serves to update the daily key limit and history
- `gkey_limit` - Optional value. sets a personal key limit for an individual participant. It does not change automatically and can only be set manually. if the field is missing, the value `config.DEFAULT_DAILY_GAME_KEYS_LIMIT` is used
- `gkey_multiplier` - Optional value. sets a personal key multiplier for an individual participant. It does not change automatically and can only be set manually. if the field is missing, the value `config.DEFAULT_USER_MULTIPLIER` is used


