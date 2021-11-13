# enverproxy

This is heavily based on the work of @MEitelwein and forked from [Enverbridge-Proxy](https://gitlab.eitelwein.net/MEitelwein/Enverbridge-Proxy).

Using this python script, you can decode the traffic between your envertech EVB202 (and probably EVB300) and envertecportal.com. All data will be send to an MQTT broker.

## How to use

### Receiving side

Install this [script](enverproxy.py) on a linux machine as a [systemd unit](enverproxy.service). Copy and update the config at [/etc/enverproxy.conf](enverproxy.conf) to your needs.

### EVB202

Restart your EVB202 and immediately press `OK` to enter the boot menu. Under `Set DHCP` set `USE DHCP` to `NO`. Under `Set Client IP` set the IP of your EVB202 to a static IP in your subnet. Under `Set Server IP` configure the IP address of your linux machine running `enverproxy.py`. Under `Set Server Mode` select `Local` as Server - yes the manual say's it's not supported for EVB202, but it works.

## Nasty details

The EVB202 will connect to the server every second - even if there is no data to transmit. This will blow up your log file if the log level is set to 3 or higher. Every 20 seconds there is a transmission of some unknown data. If the microinverter are only there will be data once every minute.

If the EVB202 is confifured to Server Mode `Local`, it will connect to the configured Server IP via TCP on port 1898. If the Server Mode is set to `Net` (the default value) it will try to connect to www.envertecportal.com via DNS and fallback to 47.91.242.120 (which is an outdated but hardcoded IP of envertecportal.com) via TCP on port 10013.

Instead of changing the Server Mode, you may also intercept the DNS query (and reply with a local IP) or redirect the TCP connection to your local machine.

There is a proxy mode, but I'm not using it, so this is totally untested.

## I've found a bug

Just open an [issue](issues/new) with as many details as possible.

## Helpful links

- [initial FHEM discussion](https://forum.fhem.de/index.php?topic=61867.0)
- [alternative to SetID](https://sven.stormbind.net/blog/posts/iot_envertech_enverbridge_evb202/)
- [lengthy discussion about EVB202](https://www.photovoltaikforum.com/thread/125652-envertech-bridge-evb202-oder-evb201/)
