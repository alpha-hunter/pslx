from pslx.micro_service.ttl_cleaner.ttl_cleaner import TTLCleaner

if __name__ == "__main__":
    ttl_cleaner = TTLCleaner()
    ttl_cleaner.set_schedule(
        hour='*',
        minute='*/10'
    )
    ttl_cleaner.set_max_instances(max_instances=5)
    ttl_cleaner.start()
