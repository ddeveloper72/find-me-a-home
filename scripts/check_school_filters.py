"""Check if school filter values match database values"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, db
from models import School

with app.app_context():
    print('Filter Test - Case Sensitivity Issue:')
    print('=' * 60)
    
    # Test Primary
    primary_upper = School.query.filter(School.school_type == 'Primary').count()
    primary_lower = School.query.filter(School.school_type == 'primary').count()
    print(f'Schools with school_type="Primary" (filter value): {primary_upper}')
    print(f'Schools with school_type="primary" (lowercase): {primary_lower}')
    
    print()
    
    # Test Post-Primary
    post_upper = School.query.filter(School.school_type == 'Post-Primary').count()
    post_lower = School.query.filter(School.school_type == 'post-primary').count()
    print(f'Schools with school_type="Post-Primary" (filter value): {post_upper}')
    print(f'Schools with school_type="post-primary" (lowercase): {post_lower}')
    
    print()
    print('=' * 60)
    print('DIAGNOSIS:')
    if primary_upper == 0 and primary_lower > 0:
        print('❌ Primary filter is broken - case mismatch!')
    if post_upper == 0 and post_lower > 0:
        print('❌ Post-Primary filter is broken - case mismatch!')
    
    print()
    print('FIX: Update template filter values to match database:')
    print('  "Primary" → "primary"')
    print('  "Post-Primary" → "post-primary"')
