from argparse import ArgumentParser
import bottle
import json
import sys

# globals
g_sysinfo_provider = None


class WindowsSystemInformationProvider(object):

    def __init__(self):
        import wmi
        self.wmi = wmi.WMI()
        self.ohm = wmi.WMI(namespace='root\\OpenHardwareMonitor')

    def get_cpu_load(self):
        """Return the current average CPU load across all processor cores"""
        wql = "SELECT * FROM Win32_PerfFormattedData_Counters_ProcessorInformation WHERE NAME = '_Total'"
        res = self.wmi.query(wql)
        return 100 - int(res[0].PercentIdleTime)

    def get_free_memory(self):
        avail_gb = self.ohm.query("select * from Sensor where Identifier = '/ram/data/0'")[0].Value  # available
        return int(avail_gb * 1024 * 1024 * 1024)

    def get_total_memory(self):
        used_gb = self.ohm.query("select * from Sensor where Identifier = '/ram/data/1'")[0].Value
        return int(used_gb * 1024 * 1024 * 1024) + self.get_free_memory()

    def get_cpu_temperature(self):
        """Get the CPU temperature in Celsius"""
        return self.ohm.query("select * from Sensor where Identifier = '/amdcpu/0/temperature/0'")[0].Value; 


class LinuxSystemInformationProvider(object):

    def __init__(self):
        import psutil
        self.psutil = psutil

    def _get_temp(self):
        import sensors
        sensors.init()
        for chip in sensors.iter_detected_chips():
            if not 'temp' in str(chip):
                continue
            tot = 0
            for i, feature in enumerate(chip):
                tot += feature.get_value()
            return float(tot) / (i + 1)
        return None

    def get_cpu_load(self):
        return self.psutil.cpu_percent(interval=1)

    def get_free_memory(self):
        return self.psutil.virtual_memory().free

    def get_total_memory(self):
        return self.psutil.virtual_memory().total

    def get_cpu_temperature(self):
        return self._get_temp()


#===============================================================================
# API Views
#===============================================================================
@bottle.route("/")
def index():
    return "Hello, world!"


@bottle.route("/api/statsdump")
def stats_dump():
    bottle.response.content_type = "application/json"
    return json.dumps({
        "cpu_load_percent": g_sysinfo_provider.get_cpu_load(),
        "total_memory": g_sysinfo_provider.get_total_memory(),
        "free_memory": g_sysinfo_provider.get_free_memory(),
        "cpu_temp_celsius": g_sysinfo_provider.get_cpu_temperature(),
    })


@bottle.route("/api/temperature")
def get_temperature():
    return json.dumps({"cpu_temp_celsius": g_sysinfo_provider.get_cpu_temperature()})


@bottle.route("/api/cpuload")
def cpu_load():
    bottle.response.content_type = "application/json"
    return json.dumps({"cpu_load_percent": g_sysinfo_provider.get_cpu_load(), })

#===============================================================================
# Plumbing
#===============================================================================
def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('-p', '--port',
                        type=int,
                        default=8080)
    return parser.parse_args()

def main():
    global g_sysinfo_provider
    args = parse_arguments()
    if sys.platform.startswith('win'):
        g_sysinfo_provider = WindowsSystemInformationProvider()
    else:
        g_sysinfo_provider = LinuxSystemInformationProvider()
    bottle.run(host='0.0.0.0', port=args.port)

if __name__ == '__main__':
    main()
