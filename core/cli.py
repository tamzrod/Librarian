"""
CLI commands for Librarian derived artifact recovery.

Usage:
    python -m core.cli repair thumbnails [--dry-run] [--fix]
    python -m core.cli repair list
    python -m core.cli detect thumbnails
"""

import argparse
import logging
import sys
from typing import Optional

from storage.postgres_backend import PostgresBackend
from core.recovery import (
    get_recovery_handler,
    RECOVERY_HANDLERS,
    ArtifactState,
)


def setup_logging(verbose: bool = False):
    """Configure logging for CLI output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def cmd_list(args):
    """List available artifact types for recovery."""
    print("\nAvailable artifact types for recovery:\n")
    print(f"  {'Artifact Type':<20} {'Handler':<20}")
    print(f"  {'-'*20} {'-'*20}")
    
    for artifact_type in RECOVERY_HANDLERS:
        print(f"  {artifact_type:<20} {RECOVERY_HANDLERS[artifact_type].__name__}")
    
    print()


def cmd_detect(args):
    """Detect artifact state for an artifact type."""
    setup_logging(args.verbose)
    
    backend = get_backend(args)
    if not backend:
        return 1
    
    handler = get_recovery_handler(args.artifact_type, backend)
    if not handler:
        print(f"Error: Unknown artifact type: {args.artifact_type}")
        print(f"Available types: {', '.join(RECOVERY_HANDLERS.keys())}")
        return 1
    
    print(f"\nDetecting {args.artifact_type} artifacts...")
    report = handler.detect()
    
    # Print summary
    summary = report.summary()
    print(f"\n{'='*60}")
    print(f"Detection Results: {args.artifact_type}")
    print(f"{'='*60}")
    print(f"  Total documents scanned:     {summary['total_documents']}")
    print(f"  Total files on disk:         {summary['total_files']}")
    print(f"  Valid artifacts:              {summary['valid']}")
    print(f"  Missing artifacts:           {summary['missing']}")
    print(f"  Orphan files:                {summary['orphans']}")
    print(f"  Health percentage:           {summary['health_percentage']}%")
    
    if summary['errors']:
        print(f"\n  Errors: {len(summary['errors'])}")
        for error in summary['errors'][:5]:
            print(f"    - {error}")
    
    # Print missing artifacts details if requested
    if report.missing and args.verbose:
        print(f"\nMissing artifacts ({len(report.missing)}):")
        for record in report.missing[:20]:
            print(f"  Document {record.document_id}: {record.reason}")
        if len(report.missing) > 20:
            print(f"  ... and {len(report.missing) - 20} more")
    
    # Print orphan files details if requested
    if report.orphans and args.verbose:
        print(f"\nOrphan files ({len(report.orphans)}):")
        for record in report.orphans[:20]:
            print(f"  {record.artifact_path}")
        if len(report.orphans) > 20:
            print(f"  ... and {len(report.orphans) - 20} more")
    
    print()
    
    backend.close()
    return 0


def cmd_repair(args):
    """Repair missing artifacts for an artifact type."""
    setup_logging(args.verbose)
    
    backend = get_backend(args)
    if not backend:
        return 1
    
    handler = get_recovery_handler(args.artifact_type, backend)
    if not handler:
        print(f"Error: Unknown artifact type: {args.artifact_type}")
        print(f"Available types: {', '.join(RECOVERY_HANDLERS.keys())}")
        return 1
    
    # First detect missing artifacts
    print(f"\nDetecting missing {args.artifact_type} artifacts...")
    report = handler.detect()
    
    if not report.missing:
        print(f"\nNo missing {args.artifact_type} artifacts found. System is healthy!")
        backend.close()
        return 0
    
    print(f"\nFound {len(report.missing)} missing {args.artifact_type} artifacts.")
    
    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")
        print("\nThe following actions would be performed:")
        for record in report.missing[:20]:
            print(f"  - Clear metadata and requeue job for document {record.document_id}")
        if len(report.missing) > 20:
            print(f"  ... and {len(report.missing) - 20} more")
        
        print(f"\nTo execute repairs, run with --fix flag:")
        print(f"  librarian repair {args.artifact_type} --fix")
    else:
        print("\n[REPAIR MODE - Changes will be made]")
        print("\nRepairing artifacts...")
        
        repair_report = handler.repair(report.missing, dry_run=False)
        
        print(f"\nRepair complete:")
        print(f"  Repaired: {repair_report.repaired}")
        print(f"  Failed:   {repair_report.failed}")
        print(f"  Skipped:  {repair_report.skipped}")
        
        if repair_report.errors:
            print(f"\nErrors encountered:")
            for error in repair_report.errors[:10]:
                print(f"  - {error}")
    
    print()
    
    backend.close()
    return 0


def get_backend(args) -> Optional[PostgresBackend]:
    """Create a backend connection from CLI arguments."""
    try:
        backend = PostgresBackend(
            host=args.db_host or 'localhost',
            port=args.db_port or 5432,
            dbname=args.db_name or 'librarian',
            user=args.db_user or 'librarian',
            password=args.db_password or 'librarian'
        )
        
        # Test connection
        conn = backend._get_connection()
        conn.close()
        
        return backend
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Librarian derived artifact recovery CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Repair command
    repair_parser = subparsers.add_parser(
        'repair',
        help='Repair missing artifacts'
    )
    repair_parser.add_argument(
        'artifact_type',
        nargs='?',
        default='thumbnail',
        help='Artifact type to repair (default: thumbnail)'
    )
    repair_parser.add_argument(
        '--fix',
        action='store_true',
        help='Actually perform repairs (default is dry-run)'
    )
    repair_parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Show what would be done without making changes (default)'
    )
    
    # Detect command
    detect_parser = subparsers.add_parser(
        'detect',
        help='Detect artifact state'
    )
    detect_parser.add_argument(
        'artifact_type',
        nargs='?',
        default='thumbnail',
        help='Artifact type to detect (default: thumbnail)'
    )
    
    # List command
    list_parser = subparsers.add_parser(
        'list',
        help='List available artifact types'
    )
    
    # Database connection options (shared)
    for p in [repair_parser, detect_parser]:
        p.add_argument('--db-host', default=None, help='Database host')
        p.add_argument('--db-port', type=int, default=None, help='Database port')
        p.add_argument('--db-name', default=None, help='Database name')
        p.add_argument('--db-user', default=None, help='Database user')
        p.add_argument('--db-password', default=None, help='Database password')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        cmd_list(args)
        return 0
    elif args.command == 'detect':
        return cmd_detect(args)
    elif args.command == 'repair':
        return cmd_repair(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
