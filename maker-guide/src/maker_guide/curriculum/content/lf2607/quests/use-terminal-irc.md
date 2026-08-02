# Use IRC from the terminal

Quest: use-terminal-irc

## Mission

Connect to classroom IRC with WeeChat. Then send the guide a private IRC message so it can verify that you are using a terminal IRC client.

## Why This Matters

The web IRC frontend is the right Day 1 support tool. This quest is different: it proves you can join the same community from a terminal client when you want a persistent workflow inside SSH.

## Commands You Will Use

- `weechat`

## Steps

1. Read the [IRC support guide](../guides/irc-support.md).
2. SSH into the classroom server.
3. Start WeeChat:

```bash
weechat
```

WeeChat commands start with `/`. Text that does not start with `/` is sent to the current channel or private conversation.

## Configure WeeChat

Do not store your classroom password directly in WeeChat's IRC config file. Store it in WeeChat secured data instead.

First, set a WeeChat secure-data passphrase. This protects secrets stored by WeeChat, and WeeChat will ask for it when it starts:

```text
/secure passphrase YOUR_WEECHAT_SECURE_DATA_PASSPHRASE
```

Store your classroom password in secured data:

```text
/secure set classroom_password YOUR_CLASSROOM_PASSWORD
```

Add the classroom IRC server:

```text
/server add kolamayermakers lf2607.kolamayermakers.org/6697 -tls
```

Tell WeeChat to log in with your classroom account. Replace `YOUR_USERNAME` with your classroom username:

```text
/set irc.server.kolamayermakers.sasl_username "YOUR_USERNAME"
/set irc.server.kolamayermakers.sasl_password "${sec.data.classroom_password}"
/set irc.server.kolamayermakers.sasl_mechanism plain
```

Set your nick to your classroom username. The server expects this:

```text
/set irc.server.kolamayermakers.nicks "YOUR_USERNAME"
```

Join the classroom channels automatically:

```text
/set irc.server.kolamayermakers.autojoin "#kolamayermakers,#lf2607"
```

Connect automatically when WeeChat starts:

```text
/set irc.server.kolamayermakers.autoconnect on
```

Connect now:

```text
/connect kolamayermakers
```

Save the configuration:

```text
/save
```

## Finish The Quest

Send the guide a private message from WeeChat:

```text
/query <guide-nick> hello from WeeChat
```

Then ask the guide to check the quest after it replies.

## Hints

1. Use Gamja at [https://lf2607.kolamayermakers.org/irc/](https://lf2607.kolamayermakers.org/irc/) if you get stuck.
2. Browser IRC does not satisfy this quest; use WeeChat.
3. The guide validates this after you message it from WeeChat.
4. If WeeChat says you are not registered or authenticated, re-check the SASL username and secured password settings above.

## If Check Fails

The guide needs to see you message it from WeeChat. If it reports a browser client or no response, reconnect with WeeChat and message the guide again.

## Related Reading

- [weechat](../commands/weechat.md)
- [irc](../concepts/irc.md)
