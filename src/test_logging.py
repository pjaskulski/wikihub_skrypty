""" test"""
import logging

# tworzenie obiektu loggera
#file_log = Path('..') / 'log' / 'ahp_zbiorcza_pkt_prng.log'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
c_handler = logging.StreamHandler()
#f_handler = logging.FileHandler(file_log)
log_format = logging.Formatter('%(asctime)s - %(message)s')
c_handler.setFormatter(log_format)
#f_handler.setFormatter(log_format)
#f_handler.setLevel(logging.INFO)
logger.addHandler(c_handler)
#logger.addHandler(f_handler)
logger.info("Początek logowania %s", 'INFO')
logger.warning("Początek logowania %s", 'WARNING')