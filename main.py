import ipaddress
import os
import telnetlib
from pprint import pprint
from time import sleep

import yaml
from jinja2 import Environment, FileSystemLoader


def send_commands_ros(host, port, commands, cr=b"\n\r", fast_pause=0.5):
    output = ""
    with telnetlib.Telnet(host, port=port) as t:
        t.write(cr)
        sleep(fast_pause)
        out = t.read_very_eager().decode().strip()
        if out[-1] == ">":
            print(f"{port} is cool")
            for command in commands:
                t.write(command.encode() + cr)
                sleep(fast_pause)
                output += t.read_very_eager().decode().strip() + "\n"
    return output


def send_commands_ios(host, port, commands, config=False, cr=b"\r\n", fast_pause=0.5):
    output = ""
    with telnetlib.Telnet(host, port=port) as t:
        sleep(fast_pause)
        lastline = t.read_very_eager().decode().splitlines()[-1]
        if "dialog" in lastline:
            t.write(b"no" + cr)
            sleep(fast_pause)
        else:
            t.write(cr)
            sleep(fast_pause)
        lastline = t.read_very_eager().decode().splitlines()[-1]
        if lastline[-1] == ">":
            print(f"{port} is cool")
            t.write(b"enable" + cr)
            sleep(fast_pause)
        elif lastline[-1] == "#":
            print(f"{port} in enable")
            if config:
                t.write(b"conf t" + cr)
                sleep(fast_pause)
            for command in commands:
                t.write(command.encode() + cr)
                sleep(fast_pause)
                output += t.read_very_eager().decode().strip() + "\n"
            if config:
                t.write(b"end" + cr)
    return output


def load_params(paramfile):
    with open(paramfile) as f:
        devices = yaml.safe_load(f)
    for dev in devices:
        dev["id"] = dev["loip"].split(".")[-1]
        for vlan in dev["vlans"]:
            if "ip" in vlan.keys():
                vlan["network"] = str(ipaddress.ip_interface(vlan["ip"]).network)
    return devices


def generate_config(template, data):
    template_dir, template_file = os.path.split(template)
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_file)
    return template.render(data)


def main():
    # ports = [32769, 32770, 32771, 32772, 32773, 32774]
    host = "10.104.10.200"
    devs = load_params("devices.yml")
    for dev in devs:
        print("#" * 80)
        print(f"Config device {dev['name']}...")
        conf = generate_config("templates/sw.j2", dev)

        out = send_commands_ros(
            host, dev["port"], [line.strip() for line in conf.splitlines()]
        )
        print(out)


def main2():
    host = "10.104.10.200"
    devs = load_params("switches.yml")

    for dev in devs:
        print("#" * 80)
        print(dev["name"])
        conf = generate_config("templates/sw.j2", dev)
        if dev["name"] in ["SW5"]:
            out = send_commands_ros(
                host, dev["port"], [line.strip() for line in conf.splitlines()]
            )
            print(out)


if __name__ == "__main__":
    commands = [
        "/int bridge add name=br1 vlan-filtering=yes",
        "/int bridge port add bridge=br1 interface=ether1",
        "/int bridge port add bridge=br1 interface=ether2",
        "/int bridge port add bridge=br1 interface=ether3",
        "/int bridge port add bridge=br1 interface=ether4",
        "/int bridge port add bridge=br1 interface=ether5",
        "/int bridge port add bridge=br1 interface=ether6",
    ]
    # main()
    # main2()
    host = "10.104.10.200"
