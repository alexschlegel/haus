import time
from copy import copy
from collections import OrderedDict
import threading
import json

import numpy as np
import matplotlib.pyplot as plt


class History(object):
    
    _data = None
    
    _getter = None
    
    _rate = None
    _next_record_time = None
    _final_record_time = None
    _should_continue = False
    _thread = None
    
    @property
    def fields(self):
        return list(self.data.keys())
    
    @property
    def data(self):
        return self._data
    
    @property
    def time(self):
        return self['time'][-1] if len(self) > 0 else None
    
    @property
    def getter(self):
        return self._getter
    
    @getter.setter
    def getter(self, getter):
        if not callable(getter):
            raise TypeError('getter must be callable')
        
        self._getter = getter
    
    @property
    def recording(self):
        return self._thread is not None
    
    def __init__(self, fields, getter=None):
        assert 'time' not in fields, 'time is added implicitly'
        fields = ['time'] + fields
        
        self.getter = getter
        
        self._set_raw_data([(field,[]) for field in fields])
    
    def add(self, **kwargs):
        if len(kwargs) == 0 and self.getter is not None:
            kwargs = self.getter()
        
        kwargs['time'] = time.time()
        
        data = self.data
        
        for field in self.fields:
            try:
                data[field].append(kwargs[field])
            except KeyError:
                raise ValueError('field "%s" is required' % (field,))
    
    def start(self, rate=1, duration=None):
        self._rate = float(rate)
        
        if not self.recording:
            self._next_record_time = time.time()
            
            if duration is not None:
                self._final_record_time = self._next_record_time + duration
            else:
                self._final_record_time = np.inf
            
            self._should_continue = True
            
            self._thread = threading.Thread(
                target=self._record_loop,
                )
            
            self._thread.daemon = True
            self._thread.start()
    
    def stop(self, wait=True):
        if self.recording:
            self._should_continue = False
            
            if wait: self._thread.join()
            
            self._next_record_time = None
            self._final_record_time = None
            self._thread = None
    
    def plot(self, fields=None, block=False):
        if fields is None: fields = [field for field in self.fields if field != 'time']
        
        data = self.data
        
        time = np.array(data['time'])
        time = time - time[0]
        
        for field in fields:
            plt.plot(time, data[field], '.')
        
        plt.legend(fields)
        
        plt.show(block=block)
    
    def save(self, path):
        raw_data = self._get_raw_data()
        
        with open(path, 'w') as f:
            json.dump(raw_data, f)
    
    def load(self, path):
        with open(path, 'r') as f:
            raw_data = json.load(f)
        
        self._set_raw_data(raw_data)
    
    def __len__(self):
        return len(self.data['time'])
    
    def __repr__(self):
        return '%s(%d) %s' % (self.__class__.__name__, len(self), ','.join(self.data.keys()))
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return self.data[key]
        else:
            return {field:value[key] for field,value in self.data.items()}
    
    def _get_raw_data(self):
        data = self.data
        return [(field,value) for field,value in data.items()]
    
    def _set_raw_data(self, raw_data):
        self._data = OrderedDict(raw_data)
    
    def _record_loop(self):
        while self._should_continue:
            t_now = time.time()
            
            while t_now < self._next_record_time:
                if t_now > self._final_record_time:
                    self.stop(wait=False)
                    return
                if not self._should_continue:
                    return
                
                time.sleep(0.001)
                t_now = time.time()
            
            self.add()
            
            self._next_record_time += 1. / self._rate
