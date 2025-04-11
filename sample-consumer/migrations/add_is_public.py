from sqlalchemy import create_engine, text

# Create engine
engine = create_engine("sqlite:///sample-consumer/users.db")

# Add is_public column
with engine.connect() as connection:
    # Check if column exists first
    result = connection.execute(text("PRAGMA table_info(prompts)"))
    columns = [row[1] for row in result]
    
    if 'is_public' not in columns:
        connection.execute(text("ALTER TABLE prompts ADD COLUMN is_public BOOLEAN DEFAULT 0"))
        connection.commit()
        print("Added is_public column to prompts table")
    else:
        print("is_public column already exists") 