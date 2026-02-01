
import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "detailed",
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:

    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("valutatrade")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    logger.handlers.clear()
    
    if log_format == "json":
        formatter = _create_json_formatter()
    elif log_format == "detailed":
        formatter = _create_detailed_formatter()
    else:
        formatter = _create_simple_formatter()
    
    log_file = os.path.join(log_dir, "actions.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def _create_simple_formatter() -> logging.Formatter:
    return logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def _create_detailed_formatter() -> logging.Formatter:
    return logging.Formatter(
        '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def _create_json_formatter() -> logging.Formatter:
    import json
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            
            if record.exc_info:
                log_record["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_record, ensure_ascii=False)
    
    return JsonFormatter()


def get_logger(name: str = "valutatrade") -> logging.Logger:
    return logging.getLogger(name)


logger = setup_logging()