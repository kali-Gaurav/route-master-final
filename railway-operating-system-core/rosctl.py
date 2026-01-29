"""Central CLI dispatcher for the Railway Operating System (rosctl).

Minimal commands implemented: generate-routes, enqueue, worker, job-status, api-start.
"""
import argparse
import json
import sys
from jobs import enqueue_job, list_jobs, get_job
from jobs import get_job_logs
from audit import record_audit
from tenants import create_tenant, list_tenants, get_tenant, deactivate_tenant
from auth import create_api_key, list_api_keys, revoke_api_key
from db_migrator import migrate_sqlite_to_postgres, verify_migration


def cmd_generate_routes(args):
    payload = {
        'source': args.source,
        'dest': args.dest,
        'date': args.date,
        'max_transfers': args.max_transfers,
        'max_results': args.max_results,
        'sort_by': args.sort_by
    }

    if args.background:
        job_id = enqueue_job('generate-routes', payload)
        print(f"Enqueued job id: {job_id}")
        try:
            record_audit('enqueue-generate-routes', user=None, details={**payload, 'job_id': job_id})
        except Exception:
            pass
        return 0

    # run inline
    from commands.generate_routes import run_generate_routes
    out_path, summary = run_generate_routes(payload)
    print('Wrote routes to:', out_path)
    print('Summary:', json.dumps(summary, indent=2))
    try:
        record_audit('generate-routes', user=None, details={**payload, 'out_path': out_path, 'summary': summary})
    except Exception:
        pass
    return 0


def cmd_job_status(args):
    rows = list_jobs(limit=args.limit)
    for r in rows:
        print(r)
    return 0


def cmd_job_log(args):
    job = get_job(args.job_id)
    if not job:
        print('Job not found')
        return 1
    print(json.dumps(job, indent=2))
    return 0


def cmd_backup_db(args):
    from commands.backup import backup_db
    out = backup_db(dest_dir=args.dest, compress=args.compress)
    if out:
        print('Backup created:', out)
        try:
            record_audit('backup-db', user=None, details={'path': out, 'compress': args.compress})
        except Exception:
            pass
        return 0
    print('Backup failed')
    return 1


def cmd_db_check(args):
    from commands.db_tools import run_db_check
    res = run_db_check()
    import json
    print(json.dumps(res, indent=2))
    try:
        record_audit('db-check', user=None, details={'result': res})
    except Exception:
        pass
    return 0


def cmd_start_worker(args):
    from ros_worker import run_worker
    run_worker(poll_interval=args.poll)
    return 0


def cmd_start_api(args):
    try:
        import uvicorn
        from ros_api import app
        uvicorn.run(app, host=args.host, port=args.port)
    except Exception as e:
        print('Failed to start API server:', e)
        return 1
    return 0


def cmd_restore_db(args):
    from commands.restore_db import restore_db
    out = restore_db(args.src, dest_db=None, force=args.force, dry_run=args.dry_run)
    if out:
        print('Restore completed:', out)
        try:
            record_audit('restore-db', user=None, details={'src': args.src, 'dest': out, 'force': args.force, 'dry_run': args.dry_run})
        except Exception:
            pass
        return 0
    print('Restore failed')
    return 1


def cmd_job_tail(args):
    rows = get_job_logs(args.job_id, limit=args.limit)
    # print oldest -> newest
    for r in reversed(rows):
        _, job_id, level, message, created_at = r
        print(f"[{created_at}] {level.upper()}: {message}")
    return 0


def cmd_create_tenant(args):
    tenant_id = create_tenant(args.name)
    if not tenant_id:
        print('Failed to create tenant')
        return 1
    api_key = create_api_key(tenant_id)
    if not api_key:
        print('Failed to create initial API key')
        return 1
    print(f"Tenant created: {tenant_id}")
    print(f"Initial API Key: {api_key}")
    try:
        record_audit('create-tenant', user=None, details={'tenant_id': tenant_id, 'name': args.name})
    except Exception:
        pass
    return 0


def cmd_list_tenants(args):
    rows = list_tenants()
    if not rows:
        print('No tenants found')
        return 0
    print(f"{'Tenant ID':<20} {'Name':<30} {'Created At'}")
    print('-' * 60)
    for id_, tenant_id, name, created_at in rows:
        print(f"{tenant_id:<20} {name:<30} {created_at}")
    return 0


def cmd_issue_key(args):
    tenant = get_tenant(args.tenant_id)
    if not tenant:
        print(f"Tenant {args.tenant_id} not found")
        return 1
    api_key = create_api_key(args.tenant_id)
    if not api_key:
        print('Failed to create API key')
        return 1
    print(f"New API Key for {args.tenant_id}: {api_key}")
    try:
        record_audit('issue-key', user=None, details={'tenant_id': args.tenant_id})
    except Exception:
        pass
    return 0


def cmd_revoke_key(args):
    keys = list_api_keys()
    found = False
    for id_, api_key, tenant_id, active, _ in keys:
        if api_key == args.api_key:
            found = True
            break
    if not found:
        print(f"API key not found")
        return 1
    if revoke_api_key(args.api_key):
        print(f"API key revoked: {args.api_key}")
        try:
            record_audit('revoke-key', user=None, details={'api_key': args.api_key[:8] + '...'})
        except Exception:
            pass
        return 0
    print('Failed to revoke API key')
    return 1


def cmd_migrate_db(args):
    """Migrate data from SQLite to PostgreSQL."""
    postgres_url = args.postgres_url
    if not postgres_url:
        print("Error: PostgreSQL URL required (--postgres-url or DATABASE_URL env var)")
        return 1
    
    print(f"Starting migration: SQLite -> PostgreSQL")
    print(f"Dry-run: {args.dry_run}")
    
    report = migrate_sqlite_to_postgres(
        postgres_url=postgres_url,
        sqlite_db=args.sqlite_db,
        dry_run=args.dry_run,
        backup_first=args.backup
    )
    
    print(json.dumps(report, indent=2))
    
    if report['status'] in ['success', 'partial_failure']:
        try:
            record_audit('migrate-db', user=None, details={'status': report['status'], 'tables_migrated': report['tables_migrated']})
        except Exception:
            pass
    
    return 0 if report['status'] == 'success' else 1


def cmd_verify_migration(args):
    """Verify data consistency between SQLite and PostgreSQL."""
    postgres_url = args.postgres_url
    if not postgres_url:
        print("Error: PostgreSQL URL required (--postgres-url or DATABASE_URL env var)")
        return 1
    
    print("Verifying migration...")
    report = verify_migration(postgres_url=postgres_url, sqlite_db=args.sqlite_db)
    print(json.dumps(report, indent=2))
    
    return 0 if report['status'] in ['verified', 'mismatch'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog='rosctl')
    sub = parser.add_subparsers(dest='cmd')

    g = sub.add_parser('generate-routes')
    g.add_argument('--source', '-s', required=True)
    g.add_argument('--dest', '-d', required=True)
    g.add_argument('--date', help='YYYY-MM-DD')
    g.add_argument('--max-transfers', type=int, default=3)
    g.add_argument('--max-results', type=int, default=100)
    g.add_argument('--sort-by', choices=['duration'], default=None)
    g.add_argument('--background', action='store_true')
    g.set_defaults(func=cmd_generate_routes)

    w = sub.add_parser('worker')
    w.add_argument('--poll', type=int, default=3)
    w.set_defaults(func=cmd_start_worker)

    j = sub.add_parser('job-status')
    j.add_argument('--limit', type=int, default=50)
    j.set_defaults(func=cmd_job_status)

    jl = sub.add_parser('job-log')
    jl.add_argument('job_id', type=int)
    jl.set_defaults(func=cmd_job_log)

    jt = sub.add_parser('job-tail')
    jt.add_argument('job_id', type=int)
    jt.add_argument('--limit', type=int, default=200)
    jt.set_defaults(func=cmd_job_tail)

    a = sub.add_parser('api-start')
    a.add_argument('--host', default='127.0.0.1')
    a.add_argument('--port', type=int, default=8000)
    a.set_defaults(func=cmd_start_api)

    # Backup DB
    b = sub.add_parser('backup-db')
    b.add_argument('--dest', default='backups')
    b.add_argument('--compress', action='store_true')
    b.set_defaults(func=cmd_backup_db)

    # DB check
    d = sub.add_parser('db-check')
    d.set_defaults(func=cmd_db_check)

    # Restore DB from backup
    r = sub.add_parser('restore-db')
    r.add_argument('src', help='Path to backup file to restore from')
    r.add_argument('--force', action='store_true', help='Overwrite DB without creating an extra backup')
    r.add_argument('--dry-run', action='store_true', help='Validate restore without writing')
    r.set_defaults(func=cmd_restore_db)

    # Tenant management
    ct = sub.add_parser('create-tenant')
    ct.add_argument('name', help='Tenant name')
    ct.set_defaults(func=cmd_create_tenant)

    lt = sub.add_parser('list-tenants')
    lt.set_defaults(func=cmd_list_tenants)

    ik = sub.add_parser('issue-key')
    ik.add_argument('tenant_id', help='Tenant ID')
    ik.set_defaults(func=cmd_issue_key)

    rk = sub.add_parser('revoke-key')
    rk.add_argument('api_key', help='API key to revoke')
    rk.set_defaults(func=cmd_revoke_key)

    # Migration commands
    mg = sub.add_parser('migrate-db')
    mg.add_argument('--postgres-url', help='PostgreSQL connection URL (or set DATABASE_URL env var)')
    mg.add_argument('--sqlite-db', default='railway_os.db', help='SQLite DB path')
    mg.add_argument('--dry-run', action='store_true', help='Validate migration without writing')
    mg.add_argument('--backup', action='store_true', help='Backup SQLite before migration')
    mg.set_defaults(func=cmd_migrate_db)

    mv = sub.add_parser('verify-migration')
    mv.add_argument('--postgres-url', help='PostgreSQL connection URL (or set DATABASE_URL env var)')
    mv.add_argument('--sqlite-db', default='railway_os.db', help='SQLite DB path')
    mv.set_defaults(func=cmd_verify_migration)

    args = parser.parse_args(argv)
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
