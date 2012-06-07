
import threading
import collections
import time
import logging

class DelayedRealTimeStream(threading.Thread):
    def __init__(self, signal_collector, callback, delay=2.0):
        threading.Thread.__init__(self)
        self.signal_collector = signal_collector
        self.callback = callback
        self.delay = delay
        
        self.stream_output_positions = collections.defaultdict(lambda: 0)
        
        self.terminate_requested = False
    
    def terminate(self):
        self.terminate_requested = True
    
    def run(self):
        # Wait so that all signal streams have been initialized
        time.sleep(self.delay + 1.0)
        
        while not self.terminate_requested:
            delayed_current_time = time.time() - self.delay
            
            for stream_name, stream in self.signal_collector.iterate_signal_streams():
                stream_start_timestamp = stream.end_timestamp - len(stream.samples) / float(stream.samplerate)
                
                stream_sample_index = int((delayed_current_time - stream_start_timestamp) * stream.samplerate)
                
                output_position = self.stream_output_positions[stream_name]
                
                if stream_sample_index > output_position:
                    if stream_sample_index < len(stream.samples):
                        delayed_value = stream.samples[stream_sample_index]
                        self.callback(stream_name, delayed_value)
                        self.stream_output_positions[stream_name] = stream_sample_index
                    else:
                        missing_seconds = (stream_sample_index - len(stream.samples)) / stream.samplerate
                        logging.warning("%s: %1.3f sec of data missing (%d %d)", stream_name, missing_seconds, stream_sample_index, output_position)
            
            for stream_name, stream in self.signal_collector.iterate_event_streams():
                output_position = self.stream_output_positions[stream_name]
                
                if len(stream) > output_position:
                    event_timestamp, event_value = stream[output_position]
                    
                    if event_timestamp <= delayed_current_time:
                        self.callback(stream_name, event_value)
                        self.stream_output_positions[stream_name] += 1
            
            time.sleep(0.01)
