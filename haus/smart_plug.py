
from pyHS100 import SmartPlug as BaseSmartPlug

from haus.datatypes import History
from haus.params import ip


class SmartPlug(BaseSmartPlug):
    
    def __init__(self):
        super(SmartPlug, self).__init__(ip_address=self._get_ip_address())
    
    def record_emeter(self, rate=1, duration=None):
        hist = History(
            fields=['power', 'current', 'voltage', 'total'],
            getter=self.get_emeter_realtime,
            )
        
        hist.start(
            rate=rate,
            duration=duration,
            )
        
        return hist
    
    def _get_ip_address(self):
        return ip['smart_plug']
