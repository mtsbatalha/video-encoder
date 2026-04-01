#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for UnifiedQueueManager compatibility methods.
Tests create_job() and add_to_queue() backward compatibility.
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

from managers.unified_queue_manager import UnifiedQueueManager


def test_compatibility_methods():
    """Test backward compatibility methods."""
    print("=" * 70)
    print("Testing UnifiedQueueManager Compatibility Methods")
    print("=" * 70)
    
    # Create manager
    print("\n1. Creating UnifiedQueueManager...")
    mgr = UnifiedQueueManager()
    print("   ✓ Manager created successfully")
    
    # Test create_job method
    print("\n2. Testing create_job() method...")
    try:
        job_id = mgr.create_job(
            input_path="/mnt/data/test_video.mp4",
            output_path="/mnt/conversions2/test_output.mp4",
            profile_id="nvidia_hevc_1080p",
            profile_name="NVIDIA Filmes 1080p HEVC"
        )
        print(f"   ✓ create_job() returned job_id: {job_id}")
    except AttributeError as e:
        print(f"   ✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False
    
    # Test add_to_queue method
    print("\n3. Testing add_to_queue() method...")
    try:
        profile = {
            'id': 'nvidia_hevc_1080p',
            'name': 'NVIDIA Filmes 1080p HEVC',
            'codec': 'hevc_nvenc'
        }
        
        position = mgr.add_to_queue(
            job_id=job_id,
            input_path="/mnt/data/test_video.mp4",
            output_path="/mnt/conversions2/test_output.mp4",
            profile=profile
        )
        print(f"   ✓ add_to_queue() returned position: {position}")
    except AttributeError as e:
        print(f"   ✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False
    
    # Verify job was created
    print("\n4. Verifying job was created...")
    job = mgr.get_job(job_id)
    if job:
        print(f"   ✓ Job found: {job.profile_name}")
        print(f"     - Input: {job.input_path}")
        print(f"     - Output: {job.output_path}")
        print(f"     - Status: {job.status}")
    else:
        print("   ✗ Job not found")
        return False
    
    # Test get_queue_length
    print("\n5. Testing get_queue_length()...")
    length = mgr.get_queue_length()
    print(f"   ✓ Queue length: {length}")
    
    # Clean up
    print("\n6. Cleaning up test data...")
    mgr.remove_job(job_id)
    print("   ✓ Test job removed")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        success = test_compatibility_methods()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
