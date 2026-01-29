"""Simple worker that polls `jobs` and runs supported commands."""
import time
import traceback
from jobs import fetch_next_job, update_job_status, append_job_log


def run_worker(poll_interval=3):
    print('ros_worker: starting (press Ctrl-C to stop)')
    try:
        while True:
            job = fetch_next_job()
            if not job:
                time.sleep(poll_interval)
                continue

            job_id = job['id']
            cmd = job['command']
            print(f"Picked job {job_id}: {cmd}")
            append_job_log(job_id, f"Picked job: {cmd}")
            update_job_status(job_id, 'running')
            append_job_log(job_id, "Job started", level='info')

            try:
                if cmd == 'generate-routes':
                    from commands.generate_routes import run_generate_routes
                    out_path, summary = run_generate_routes(job['payload'])
                    update_job_status(job_id, 'success', result=summary)
                    append_job_log(job_id, f"Job succeeded, output: {out_path}", level='info')
                    print(f"Job {job_id} succeeded, output: {out_path}")
                else:
                    msg = 'unknown command'
                    update_job_status(job_id, 'failed', result={'error': msg})
                    append_job_log(job_id, f"Job failed: {msg}", level='error')
            except Exception as exc:
                tb = traceback.format_exc()
                update_job_status(job_id, 'failed', result={'error': str(exc), 'trace': tb})
                append_job_log(job_id, f"Job failed with exception: {exc}\n{tb}", level='error')
                print(f"Job {job_id} failed: {exc}")

    except KeyboardInterrupt:
        print('ros_worker: stopping')
