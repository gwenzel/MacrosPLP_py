import logging
import time
import enlighten

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Setup progress bar
manager = enlighten.get_manager()
pbar = manager.counter(total=100, desc='Ticks', unit='ticks')

for i in range(1, 101):
    #logger.info("Processing step %s" % i)
    time.sleep(.2)
    pbar.update()