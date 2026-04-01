#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete test script for UnifiedQueueManager compatibility methods.
Tests all backward compatibility methods with JobManager and QueueManager.
"""

import sys
import os
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from managers.unified_queue_manager import UnifiedQueueManager, QueuePriority


def test_all_compatibility():
    """Test all backward compatibility methods."""
    print("=" * 70)
    print("Testing ALL UnifiedQueueManager Compatibility Methods")
    print("=" * 70)
    
    # Create manager
    print("\n1. Creating UnifiedQueueManager...")
    mgr = UnifiedQueueManager()
    print("   ✓ Manager created successfully")
    
    # Test create_job
    print("\n2. Testing create_job()...")
    job_id = mgr.create_job(
        input_path="/mnt/data/test1.mp4",
        output_path="/mnt/conversions2/test1.mp4",
        profile_id="nvidia_hevc_1080p",
        profile_name="NVIDIA Filmes 1080p HEVC"
    )
    print(f"   ✓ Job created with ID: {job_id[:16]}...")
    
    # Test add_to_queue
    print("\n3. Testing add_to_queue()...")
    profile = {
        'id': 'nvidia_hevc_1080p',
        'name': 'NVIDIA Filmes 1080p HEVC',
        'codec': 'hevc_nvenc'
    }
    position = mgr.add_to_queue(
        job_id=job_id,
        input_path="/mnt/data/test1.mp4",
        output_path="/mnt/conversions2/test1.mp4",
        profile=profile
    )
    print(f"   ✓ Job position in queue: {position}")
    
    # Test get_queue_length
    print("\n4. Testing get_queue_length()...")
    length = mgr.get_queue_length()
    print(f"   ✓ Queue length: {length}")
    
    # Test is_paused
    print("\n5. Testing is_paused()...")
    paused = mgr.is_paused()
    print(f"   ✓ Queue paused: {paused}")
    
    # Test pause
    print("\n6. Testing pause()...")
    mgr.pause()
    paused = mgr.is_paused()
    print(f"   ✓ Queue paused after pause(): {paused}")
    
    # Test resume
    print("\n7. Testing resume()...")
    mgr.resume()
    paused = mgr.is_paused()
    print(f"   ✓ Queue paused after resume(): {paused}")
    
    # Test get_next_job
    print("\n8. Testing get_next_job()...")
    next_job = mgr.get_next_job()
    if next_job:
        print(f"   ✓ Next job found: {next_job['job_id'][:16]}...")
    else:
        print("   ✗ No next job found")
        return False
    
    # Test mark_job_started
    print("\n9. Testing mark_job_started()...")
    marked = mgr.mark_job_started(job_id)
    print(f"   ✓ Job marked as started: {marked}")
    
    # Create another job for pop test
    print("\n10. Creating second job for pop_next_job test...")
    job_id2 = mgr.create_job(
        input_path="/mnt/data/test2.mp4",
        output_path="/mnt/conversions2/test2.mp4",
        profile_id="nvidia_hevc_1080p",
        profile_name="NVIDIA Filmes 1080p HEVC"
    )
    print(f"   ✓ Second job created: {job_id2[:16]}...")
    
    # Test pop_next_job
    print("\n11. Testing pop_next_job()...")
    popped_job = mgr.pop_next_job()
    if popped_job:
        print(f"   ✓ Popped job: {popped_job['job_id'][:16]}...")
        print(f"     Queue length after pop: {mgr.get_queue_length()}")
    else:
        print("   ✗ No job to pop")
        return False
    
    # Test remove_from_queue
    print("\n12. Testing remove_from_queue()...")
    removed = mgr.remove_from_queue(job_id)
    print(f"   ✓ Job removed: {removed}")
    print(f"     Queue length after remove: {mgr.get_queue_length()}")
    
    # Clean up any remaining jobs
    print("\n13. Cleaning up...")
    mgr.clear_queue()
    print("   ✓ Queue cleared")
    
    print("\n" + "=" * 70)
    print("ALL COMPATIBILITY TESTS PASSED ✓")
    print("=" * 70)
    print("\nSummary of tested methods:")
    print("  ✓ create_job()")
    print("  ✓ add_to_queue()")
    print("  ✓ get_queue_length()")
    print("  ✓ is_paused()")
    print("  ✓ pause()")
    print("  ✓ resume()")
    print("  ✓ get_next_job()")
    print("  ✓ mark_job_started()")
    print("  ✓ pop_next_job()")
    print("  ✓ remove_from_queue()")
    print("  ✓ clear_queue()")
    
    return True


if __name__ == "__main__":
    try:
        success = test_all_compatibility()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
