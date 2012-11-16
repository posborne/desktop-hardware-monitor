from argparse import ArgumentParser
import bottle
import json
import subprocess
import wmi

wmi_computer = wmi.WMI()
ohm = wmi.WMI(namespace='root\\OpenHardwareMonitor')


def get_cpu_load():
    """Return the current average CPU load across all processor cores"""
    wql = "SELECT * FROM Win32_PerfFormattedData_Counters_ProcessorInformation WHERE NAME = '_Total'"
    res = wmi_computer.query(wql)
    return 100 - int(res[0].PercentIdleTime)

def get_free_memory():
    return int(wmi_computer.Win32_OperatingSystem()[0].FreePhysicalMemory)

def get_total_memory():
    return int(wmi_computer.Win32_ComputerSystem()[0].TotalPhysicalMemory)

def get_cpu_temperature():
    """Get the CPU temperature in Celsius"""
    return ohm.query("select * from Sensor where Identifier = '/amdcpu/0/temperature/0'")[0].Value; 

get_cpu_temperature()

@bottle.route("/")
def index():
    return "Hello, world!"


@bottle.route("/api/statsdump")
def stats_dump():
    bottle.response.content_type = "application/json"
    return json.dumps({
        "cpu_load_percent": get_cpu_load(),
        "total_memory": get_total_memory(),
        "free_memory": get_free_memory(),
        "cpu_temp_celsius": get_cpu_temperature(),
    })


@bottle.route("/api/temperature")
def get_temperature():
    return json.dumps({"cpu_temp_celsius": get_cpu_temperature()})


@bottle.route("/api/cpuload")
def cpu_load():
    bottle.response.content_type = "application/json"
    return json.dumps({"cpu_load_percent": get_cpu_load(), })


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('-p', '--port',
                        type=int,
                        default=8080)
    return parser.parse_args()

def main():
    args = parse_arguments()
    bottle.run(host='0.0.0.0', port=args.port)

if __name__ == '__main__':
    main()
