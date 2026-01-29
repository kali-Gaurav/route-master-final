import inspect
import jobs
print('module file:', jobs.__file__)
print('members:', sorted([n for n in dir(jobs) if n.startswith('ensure_') or n.startswith('append_') or n.startswith('get_job') or n.startswith('get_job_logs')]))
print('\n--- END ---')
