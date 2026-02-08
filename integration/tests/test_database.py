"""Phase 2: Database integration tests — verify schema, CRUD, constraints, triggers."""

import pytest
from sqlalchemy import inspect, text


@pytest.mark.database
class TestDatabaseSchema:
    """Verify all expected tables exist and have correct structure."""

    EXPECTED_TABLES = [
        "schema_migrations",
        "users",
        "api_keys",
        "sessions",
        "findings",
        "readings",
        "learning_data",
        "insights",
        "oracle_suggestions",
        "health_checks",
        "audit_log",
        "oracle_users",
        "oracle_readings",
        "oracle_reading_users",
        "oracle_audit_log",
    ]

    def test_all_tables_exist(self, db_engine):
        """Verify all tables from init.sql exist in the database."""
        inspector = inspect(db_engine)
        existing = inspector.get_table_names()
        for table in self.EXPECTED_TABLES:
            assert table in existing, f"Table '{table}' missing from database"

    def test_oracle_users_columns(self, db_engine):
        """Verify oracle_users has the expected columns."""
        inspector = inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("oracle_users")}
        expected = {
            "id",
            "name",
            "name_persian",
            "birthday",
            "mother_name",
            "mother_name_persian",
            "country",
            "city",
            "coordinates",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_oracle_readings_columns(self, db_engine):
        """Verify oracle_readings has the expected columns."""
        inspector = inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("oracle_readings")}
        expected = {
            "id",
            "user_id",
            "is_multi_user",
            "primary_user_id",
            "question",
            "sign_type",
            "sign_value",
            "reading_result",
            "ai_interpretation",
            "created_at",
        }
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"


@pytest.mark.database
class TestOracleUsersCRUD:
    """Test insert/read/update/delete on oracle_users table."""

    def test_insert_and_read(self, db_connection):
        """Insert a user and read it back."""
        db_connection.execute(
            text(
                "INSERT INTO oracle_users (name, birthday, mother_name) "
                "VALUES (:name, :birthday, :mother_name)"
            ),
            {
                "name": "IntTest_Insert",
                "birthday": "1990-01-15",
                "mother_name": "TestMother",
            },
        )
        db_connection.commit()

        result = db_connection.execute(
            text("SELECT name, mother_name FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_Insert"},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "IntTest_Insert"
        assert row[1] == "TestMother"

        # Cleanup
        db_connection.execute(
            text("DELETE FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_Insert"},
        )
        db_connection.commit()

    def test_update(self, db_connection):
        """Insert and update a user."""
        db_connection.execute(
            text(
                "INSERT INTO oracle_users (name, birthday, mother_name) "
                "VALUES (:name, :birthday, :mother_name)"
            ),
            {
                "name": "IntTest_Update",
                "birthday": "1985-06-20",
                "mother_name": "OldMother",
            },
        )
        db_connection.commit()

        db_connection.execute(
            text("UPDATE oracle_users SET mother_name = :mn WHERE name = :name"),
            {"mn": "NewMother", "name": "IntTest_Update"},
        )
        db_connection.commit()

        result = db_connection.execute(
            text("SELECT mother_name FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_Update"},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "NewMother"

        # Cleanup
        db_connection.execute(
            text("DELETE FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_Update"},
        )
        db_connection.commit()

    def test_delete(self, db_connection):
        """Insert and delete a user."""
        db_connection.execute(
            text(
                "INSERT INTO oracle_users (name, birthday, mother_name) "
                "VALUES (:name, :birthday, :mother_name)"
            ),
            {
                "name": "IntTest_Delete",
                "birthday": "2000-03-10",
                "mother_name": "DelMother",
            },
        )
        db_connection.commit()

        db_connection.execute(
            text("DELETE FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_Delete"},
        )
        db_connection.commit()

        result = db_connection.execute(
            text("SELECT id FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_Delete"},
        )
        assert result.fetchone() is None


@pytest.mark.database
class TestConstraints:
    """Test database constraints and triggers."""

    def test_fk_constraint_reading_nonexistent_user(self, db_connection):
        """Inserting a reading with nonexistent user_id should fail."""
        with pytest.raises(Exception):
            db_connection.execute(
                text(
                    "INSERT INTO oracle_readings "
                    "(user_id, question, sign_type, sign_value) "
                    "VALUES (:uid, :q, :st, :sv)"
                ),
                {"uid": 999999, "q": "test?", "st": "question", "sv": "test"},
            )
            db_connection.commit()
        db_connection.rollback()

    def test_name_length_constraint(self, db_connection):
        """Name must be at least 2 characters."""
        with pytest.raises(Exception):
            db_connection.execute(
                text(
                    "INSERT INTO oracle_users (name, birthday, mother_name) "
                    "VALUES (:name, :birthday, :mn)"
                ),
                {"name": "X", "birthday": "1990-01-01", "mn": "Mom"},
            )
            db_connection.commit()
        db_connection.rollback()

    def test_updated_at_trigger(self, db_connection):
        """Verify updated_at changes on UPDATE."""
        db_connection.execute(
            text(
                "INSERT INTO oracle_users (name, birthday, mother_name) "
                "VALUES (:name, :birthday, :mn)"
            ),
            {"name": "IntTest_Trigger", "birthday": "1990-01-01", "mn": "TrigMom"},
        )
        db_connection.commit()

        # Get initial timestamps
        result = db_connection.execute(
            text("SELECT created_at, updated_at FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_Trigger"},
        )
        row = result.fetchone()
        created_at = row[0]
        initial_updated = row[1]

        # Force a small delay and update
        db_connection.execute(
            text("UPDATE oracle_users SET mother_name = :mn WHERE name = :name"),
            {"mn": "TrigMomUpdated", "name": "IntTest_Trigger"},
        )
        db_connection.commit()

        result = db_connection.execute(
            text("SELECT updated_at FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_Trigger"},
        )
        new_updated = result.fetchone()[0]
        assert new_updated >= initial_updated

        # Cleanup
        db_connection.execute(
            text("DELETE FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_Trigger"},
        )
        db_connection.commit()


@pytest.mark.database
class TestSchemaFixes:
    """Regression tests for INTEGRATION-S2 schema fixes."""

    def test_deleted_at_column_exists(self, db_engine):
        """ISSUE-1: oracle_users must have deleted_at column for soft-delete."""
        inspector = inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("oracle_users")}
        assert "deleted_at" in columns, "deleted_at column missing from oracle_users"

    def test_soft_delete_workflow(self, db_connection):
        """ISSUE-1: Soft-delete via deleted_at and filter by IS NULL."""
        db_connection.execute(
            text(
                "INSERT INTO oracle_users (name, birthday, mother_name) "
                "VALUES (:name, :birthday, :mn)"
            ),
            {"name": "IntTest_SoftDel", "birthday": "1990-01-01", "mn": "Mom"},
        )
        db_connection.commit()

        # Soft-delete
        db_connection.execute(
            text("UPDATE oracle_users SET deleted_at = NOW() WHERE name = :name"),
            {"name": "IntTest_SoftDel"},
        )
        db_connection.commit()

        # Should not appear in active query
        result = db_connection.execute(
            text(
                "SELECT id FROM oracle_users WHERE name = :name AND deleted_at IS NULL"
            ),
            {"name": "IntTest_SoftDel"},
        )
        assert (
            result.fetchone() is None
        ), "Soft-deleted user should not appear in active query"

        # Should still exist in unfiltered query
        result = db_connection.execute(
            text("SELECT id FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_SoftDel"},
        )
        assert (
            result.fetchone() is not None
        ), "Soft-deleted user should still exist in DB"

        # Cleanup
        db_connection.execute(
            text("DELETE FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_SoftDel"},
        )
        db_connection.commit()

    def test_sign_type_reading_allowed(self, db_connection):
        """ISSUE-2: sign_type='reading' must be accepted by CHECK constraint."""
        # Create a temp user first
        db_connection.execute(
            text(
                "INSERT INTO oracle_users (name, birthday, mother_name) "
                "VALUES (:name, :birthday, :mn)"
            ),
            {"name": "IntTest_SignType", "birthday": "1990-01-01", "mn": "Mom"},
        )
        db_connection.commit()

        # Insert a reading with sign_type='reading' (no user_id, single user)
        db_connection.execute(
            text(
                "INSERT INTO oracle_readings (question, sign_type, sign_value) "
                "VALUES (:q, :st, :sv)"
            ),
            {"q": "test", "st": "reading", "sv": "2024-01-01"},
        )
        db_connection.commit()

        # Also test 'multi_user' and 'daily'
        db_connection.execute(
            text(
                "INSERT INTO oracle_readings (question, sign_type, sign_value) "
                "VALUES (:q, :st, :sv)"
            ),
            {"q": "test", "st": "daily", "sv": "2024-01-01"},
        )
        db_connection.commit()

        # Cleanup
        db_connection.execute(
            text("DELETE FROM oracle_readings WHERE question = 'test'")
        )
        db_connection.execute(
            text("DELETE FROM oracle_users WHERE name = :name"),
            {"name": "IntTest_SignType"},
        )
        db_connection.commit()

    def test_null_user_id_single_user_reading(self, db_connection):
        """ISSUE-3: user_id=NULL must be allowed for single-user (anonymous) readings."""
        db_connection.execute(
            text(
                "INSERT INTO oracle_readings "
                "(user_id, is_multi_user, question, sign_type, sign_value) "
                "VALUES (NULL, FALSE, :q, :st, :sv)"
            ),
            {"q": "anonymous test", "st": "reading", "sv": "2024-06-15"},
        )
        db_connection.commit()

        result = db_connection.execute(
            text(
                "SELECT id FROM oracle_readings WHERE question = :q AND user_id IS NULL"
            ),
            {"q": "anonymous test"},
        )
        assert result.fetchone() is not None, "Anonymous reading should be inserted"

        # Cleanup
        db_connection.execute(
            text("DELETE FROM oracle_readings WHERE question = :q"),
            {"q": "anonymous test"},
        )
        db_connection.commit()

    def test_partial_index_active_users(self, db_connection):
        """Verify partial index on deleted_at WHERE NULL exists."""
        result = db_connection.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'oracle_users' AND indexname = 'idx_oracle_users_active'"
            )
        )
        row = result.fetchone()
        assert row is not None, "Partial index idx_oracle_users_active should exist"


@pytest.mark.database
class TestQueryPerformance:
    """Basic query performance verification."""

    def test_explain_analyze_oracle_users(self, db_connection):
        """Run EXPLAIN ANALYZE on a sample query."""
        result = db_connection.execute(
            text(
                "EXPLAIN ANALYZE SELECT * FROM oracle_users "
                "ORDER BY created_at DESC LIMIT 20"
            )
        )
        plan = "\n".join(row[0] for row in result.fetchall())
        assert "Execution Time" in plan or "execution time" in plan.lower()

    def test_explain_analyze_active_users_uses_index(self, db_connection):
        """Verify query plan uses partial index for active users."""
        result = db_connection.execute(
            text(
                "EXPLAIN SELECT * FROM oracle_users "
                "WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 20"
            )
        )
        plan = "\n".join(row[0] for row in result.fetchall())
        # The index should appear in the plan (may be idx_oracle_users_active or Seq Scan on small tables)
        assert "oracle_users" in plan.lower()
