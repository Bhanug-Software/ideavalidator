from app.memory.memory_store import (
    get_db_connection,
    save_conversation,
    save_message,
    load_conversations,
    load_conversation_messages,
    update_conversation_status
)

print("=" * 70)
print("TESTING DATABASE FUNCTIONS")
print("=" * 70)

# Test 1: Connection
print("\n1. Testing database connection...")
try:
    conn = get_db_connection()
    print("   ✅ Connection successful!")
    conn.close()
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    exit()

# Test 2: Save conversation
print("\n2. Testing save_conversation()...")
try:
    conv_id = save_conversation(
        "Test app idea for learning",
        "Build it"
    )
    print(f"   ✅ Conversation saved with ID: {conv_id}")
except Exception as e:
    print(f"   ❌ Save failed: {e}")
    exit()

# Test 3: Save messages
print("\n3. Testing save_message()...")
try:
    msg1 = save_message(conv_id, "user", "Test app idea for learning")
    msg2 = save_message(conv_id, "assistant", "Great idea! This is a test.")
    print(f"   ✅ Messages saved with IDs: {msg1}, {msg2}")
except Exception as e:
    print(f"   ❌ Save message failed: {e}")
    exit()

# Test 4: Load conversations
print("\n4. Testing load_conversations()...")
try:
    convs = load_conversations()
    print(f"   ✅ Loaded {len(convs)} conversations")
    for conv in convs[:2]:  # Show first 2
        print(f"      - ID: {conv['id']}, Idea: {conv['project_idea'][:40]}...")
except Exception as e:
    print(f"   ❌ Load conversations failed: {e}")

# Test 5: Load messages for conversation
print("\n5. Testing load_conversation_messages()...")
try:
    messages = load_conversation_messages(conv_id)
    print(f"   ✅ Loaded {len(messages)} messages")
    for msg in messages:
        print(f"      - {msg['role']}: {msg['content'][:40]}...")
except Exception as e:
    print(f"   ❌ Load messages failed: {e}")

# Test 6: Update status
print("\n6. Testing update_conversation_status()...")
try:
    success = update_conversation_status(conv_id, "completed")
    if success:
        print(f"   ✅ Status updated to completed")
    else:
        print(f"   ❌ Status update returned False")
except Exception as e:
    print(f"   ❌ Update status failed: {e}")

print("\n" + "=" * 70)
print("ALL TESTS COMPLETE!")
print("=" * 70)
