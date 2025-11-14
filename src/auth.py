"""Authentication and authorization utilities for the expense tracker."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Optional

from mysql.connector import Error

from .db import db_cursor
from .logger import get_logger

logger = get_logger("auth")


class AuthenticationError(RuntimeError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(RuntimeError):
    """Raised when authorization fails."""

    pass


@dataclass(frozen=True)
class UserSession:
    """Represents an authenticated user session."""

    userid: int
    email: str
    name: str
    role: str


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash a password using SHA-256 with salt.
    
    Args:
        password: Plain text password to hash.
        salt: Optional salt. If None, generates a new random salt.
    
    Returns:
        Tuple of (hashed_password, salt) as hex strings.
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine password and salt
    salted_password = password + salt
    # Hash using SHA-256
    hashed = hashlib.sha256(salted_password.encode("utf-8")).hexdigest()
    
    return hashed, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a password against a stored hash and salt.
    
    Args:
        password: Plain text password to verify.
        stored_hash: Previously hashed password.
        salt: Salt used during hashing.
    
    Returns:
        True if password matches, False otherwise.
    """
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == stored_hash


def register_user(
    name: str,
    email: str,
    password: str,
    contact: Optional[str] = None,
    role: str = "user",
) -> int:
    """Register a new user with hashed password.
    
    Args:
        name: User's full name.
        email: User's email address (must be unique).
        password: Plain text password (will be hashed).
        contact: Optional contact number.
        role: User role (default: 'user').
    
    Returns:
        The newly created user ID.
    
    Raises:
        AuthenticationError: If registration fails (e.g., email already exists).
    """
    # Check if email already exists
    check_query = "SELECT userid FROM user WHERE email = %s"
    try:
        with db_cursor() as (_, cursor):
            cursor.execute(check_query, (email,))
            if cursor.fetchone():
                raise AuthenticationError(f"Email {email} is already registered.")
    except Error as exc:
        raise AuthenticationError(f"Database error during registration check: {exc}") from exc
    
    # Hash the password
    password_hash, salt = hash_password(password)
    
    # Insert user
    user_query = """
        INSERT INTO user (name, email, contact)
        VALUES (%s, %s, %s)
    """
    
    # Insert login credentials
    login_query = """
        INSERT INTO login (userid, password, role)
        VALUES (%s, %s, %s)
    """
    
    try:
        with db_cursor(commit=True) as (conn, cursor):
            cursor.execute(user_query, (name, email, contact))
            userid = cursor.lastrowid
            
            # Store password as hash:salt format for easy retrieval
            stored_password = f"{password_hash}:{salt}"
            cursor.execute(login_query, (userid, stored_password, role))
            
            logger.info(f"User registered: {email} (ID: {userid})")
            return userid
    except Error as exc:
        raise AuthenticationError(f"Failed to register user: {exc}") from exc


def authenticate_user(email: str, password: str) -> Optional[UserSession]:
    """Authenticate a user by email and password.
    
    Args:
        email: User's email address.
        password: Plain text password.
    
    Returns:
        UserSession if authentication succeeds, None otherwise.
    """
    query = """
        SELECT u.userid, u.email, u.name, l.password, l.role
        FROM user u
        JOIN login l ON u.userid = l.userid
        WHERE u.email = %s
    """
    
    try:
        with db_cursor() as (_, cursor):
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"Authentication failed: email not found: {email}")
                return None
            
            userid, email, name, stored_password, role = row
            
            # Parse stored password (format: hash:salt)
            if ":" not in stored_password:
                # Legacy plaintext password - migrate it
                logger.warning(f"Legacy plaintext password detected for user {email}, migrating...")
                password_hash, salt = hash_password(password)
                stored_password = f"{password_hash}:{salt}"
                
                # Update the password in database
                update_query = "UPDATE login SET password = %s WHERE userid = %s"
                with db_cursor(commit=True) as (_, update_cursor):
                    update_cursor.execute(update_query, (stored_password, userid))
                
                # For legacy passwords, check if plaintext matches
                if stored_password.split(":")[0] == password:
                    return UserSession(userid=userid, email=email, name=name, role=role)
                return None
            
            stored_hash, salt = stored_password.split(":", 1)
            
            if verify_password(password, stored_hash, salt):
                logger.info(f"User authenticated: {email} (ID: {userid})")
                return UserSession(userid=userid, email=email, name=name, role=role)
            
            logger.warning(f"Authentication failed: invalid password for {email}")
            return None
            
    except Error as exc:
        logger.error(f"Database error during authentication: {exc}")
        return None


def change_password(userid: int, old_password: str, new_password: str) -> bool:
    """Change a user's password.
    
    Args:
        userid: User ID.
        old_password: Current password for verification.
        new_password: New password to set.
    
    Returns:
        True if password was changed, False if old password was incorrect.
    
    Raises:
        AuthenticationError: If database operation fails.
    """
    # First verify old password
    query = "SELECT password FROM login WHERE userid = %s"
    
    try:
        with db_cursor() as (_, cursor):
            cursor.execute(query, (userid,))
            row = cursor.fetchone()
            
            if not row:
                raise AuthenticationError("User not found.")
            
            stored_password = row[0]
            
            # Handle legacy plaintext or hashed passwords
            if ":" in stored_password:
                stored_hash, salt = stored_password.split(":", 1)
                if not verify_password(old_password, stored_hash, salt):
                    return False
            else:
                # Legacy plaintext
                if stored_password != old_password:
                    return False
            
            # Hash new password
            new_hash, new_salt = hash_password(new_password)
            new_stored = f"{new_hash}:{new_salt}"
            
            # Update password
            update_query = "UPDATE login SET password = %s WHERE userid = %s"
            with db_cursor(commit=True) as (_, update_cursor):
                update_cursor.execute(update_query, (new_stored, userid))
            
            logger.info(f"Password changed for user ID: {userid}")
            return True
            
    except Error as exc:
        raise AuthenticationError(f"Failed to change password: {exc}") from exc


def get_user_role(userid: int) -> Optional[str]:
    """Get the role of a user.
    
    Args:
        userid: User ID.
    
    Returns:
        User role or None if user not found.
    """
    query = "SELECT role FROM login WHERE userid = %s"
    
    try:
        with db_cursor() as (_, cursor):
            cursor.execute(query, (userid,))
            row = cursor.fetchone()
            return row[0] if row else None
    except Error as exc:
        logger.error(f"Error fetching user role: {exc}")
        return None


def require_role(user_session: UserSession, required_role: str) -> None:
    """Check if a user session has the required role.
    
    Args:
        user_session: Current user session.
        required_role: Required role (e.g., 'admin').
    
    Raises:
        AuthorizationError: If user doesn't have required role.
    """
    if user_session.role != required_role:
        raise AuthorizationError(
            f"Access denied. Required role: {required_role}, "
            f"user role: {user_session.role}"
        )

