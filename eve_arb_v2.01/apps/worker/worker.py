import argparse
import time

from worker_app.jobs.ingest_market import ingest_market
from worker_app.jobs.rebuild_loads import rebuild_loads
from worker_app.jobs.update_patterns import update_patterns

def run_once() -> None:
    print("worker: starting one-shot run")
    ingest_market()
    rebuild_loads()
    update_patterns()
    print("worker: one-shot run complete")

def run_loop(interval_seconds: int) -> None:
    while True:
        run_once()
        print(f"worker: sleeping {interval_seconds} seconds")
        time.sleep(interval_seconds)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["run_once", "loop"], default="run_once")
    parser.add_argument("--interval", type=int, default=900)
    args = parser.parse_args()

    if args.mode == "loop":
        run_loop(args.interval)
    else:
        run_once()

if __name__ == "__main__":
    main()
