import ipaddress
import os
import telnetlib
from pprint import pprint
from time import sleep

import yaml
from jinja2 import Environment, FileSystemLoader


def send_commands_ros(host, port, commands, cr=b"\n\r"):
    t = telnetlib.Telnet(host, port=port)
    t.write(cr)
    sleep(0.5)
    out = t.read_very_eager().decode().strip()
    output = ""
    if out[-1] == ">":
        print(f"{port} is cool")
        for command in commands:
            t.write(command.encode() + cr)
            sleep(1)
            output += t.read_very_eager().decode().strip() + "\n"
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
        conf = generate_config("templates/sw_vl.j2", dev)
        if dev["name"] in ["SW2", "SW5"]:
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
    main2()
