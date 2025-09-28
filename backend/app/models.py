import uuid
from datetime import datetime, timezone
from typing import Literal, Union, List, Optional, Dict, Any
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Column, JSON


def utc_now():
    return datetime.now(timezone.utc)


# ===== 枚举定义 =====
class UserType(str, Enum):
    GUEST = "guest"
    REGULAR = "regular"


class Visibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ===== 用户模型 =====
class UserBase(SQLModel):
    email: str = Field(max_length=64, unique=True, index=True)
    password: Optional[str] = Field(default=None, max_length=64)
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=64)


class UserRegister(SQLModel):
    email: EmailStr = Field(description="用户邮箱")
    password: str = Field(min_length=8, max_length=64, description="用户密码")
    confirm_password: str = Field(min_length=8, max_length=64, description="确认密码")


class User(UserBase, table=True):
    __tablename__ = "User"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Relationships
    chats: list["Chat"] = Relationship(back_populates="user", cascade_delete=True)
    documents: list["Document"] = Relationship(back_populates="user", cascade_delete=True)
    suggestions: list["Suggestion"] = Relationship(back_populates="user", cascade_delete=True)


class UserPublic(UserBase):
    id: uuid.UUID


# ===== 聊天模型 =====
class ChatBase(SQLModel):
    title: str = Field(max_length=255)
    visibility: Visibility = Field(default=Visibility.PRIVATE)


class ChatCreate(ChatBase):
    pass


class Chat(ChatBase, table=True):
    __tablename__ = "Chat"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="User.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utc_now)
    last_context: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="chats")
    messages: list["Message"] = Relationship(back_populates="chat", cascade_delete=True)
    votes: list["Vote"] = Relationship(back_populates="chat", cascade_delete=True)


class ChatPublic(ChatBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


# ===== 消息模型 =====
class MessageBase(SQLModel):
    role: MessageRole
    parts: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    attachments: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))


class MessageCreate(MessageBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)


class Message(MessageBase, table=True):
    __tablename__ = "Message_v2"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    chat_id: uuid.UUID = Field(foreign_key="Chat.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    chat: Optional[Chat] = Relationship(back_populates="messages")
    votes: list["Vote"] = Relationship(back_populates="message", cascade_delete=True)


class MessagePublic(MessageBase):
    id: uuid.UUID
    chat_id: uuid.UUID
    created_at: datetime


# ===== 聊天请求模型 =====
class ChatRequest(SQLModel):
    id: uuid.UUID
    message: MessageCreate
    selectedChatModel: str = "gpt-4"
    selectedVisibilityType: Visibility = Field(default=Visibility.PRIVATE)


# ===== 认证模型 =====
class LoginRequest(SQLModel):
    email: str
    password: str


class LoginResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


# 访客登录功能已取消


class RegisterResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
    message: str = "注册成功"


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: Optional[str] = None
    type: Optional[str] = None


# ===== AI工具模型 =====
class ImageGenerationRequest(SQLModel):
    prompt: str = Field(description="图片描述文本")
    style: str = "realistic"  # realistic, artistic, cartoon, abstract
    size: str = "1024x1024"   # 512x512, 768x768, 1024x1024


class ImageGenerationResponse(SQLModel):
    success: bool
    result: Dict[str, Any]
    prompt: str
    style: str
    size: str


class ContentRewriteRequest(SQLModel):
    originalContent: str = Field(description="原始内容")
    rewriteType: str = "improve_clarity"  # improve_clarity, make_professional, etc.
    targetTone: Optional[str] = None      # professional, casual, friendly, etc.
    targetAudience: Optional[str] = None
    additionalInstructions: Optional[str] = None


class ContentRewriteResponse(SQLModel):
    success: bool
    originalContent: str
    rewrittenContent: str
    rewriteType: str
    targetTone: Optional[str] = None
    targetAudience: Optional[str] = None
    originalLength: int
    rewrittenLength: int


# ===== 文件上传模型 =====
class FileUploadResponse(SQLModel):
    success: bool
    filename: str
    url: str
    size: int
    contentType: str


# ===== 文档模型 =====
class DocumentKind(str, Enum):
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    SHEET = "sheet"


class DocumentBase(SQLModel):
    title: str
    content: Optional[str] = None
    kind: DocumentKind = Field(default=DocumentKind.TEXT)


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    title: Optional[str] = None
    content: Optional[str] = None
    kind: Optional[DocumentKind] = None


class Document(DocumentBase, table=True):
    __tablename__ = "Document"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="User.id", nullable=False, ondelete="CASCADE")

    # Relationships
    user: Optional[User] = Relationship(back_populates="documents")


class DocumentPublic(DocumentBase):
    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID


class DocumentRequest(SQLModel):
    title: str
    content: str
    kind: DocumentKind = Field(default=DocumentKind.TEXT)


# ===== 投票模型 =====
class VoteBase(SQLModel):
    is_upvoted: bool


class VoteRequest(SQLModel):
    chatId: uuid.UUID
    messageId: uuid.UUID
    type: str  # "up" or "down"


class Vote(VoteBase, table=True):
    __tablename__ = "Vote_v2"

    chat_id: uuid.UUID = Field(foreign_key="Chat.id", primary_key=True)
    message_id: uuid.UUID = Field(foreign_key="Message_v2.id", primary_key=True)

    # Relationships
    chat: Optional[Chat] = Relationship(back_populates="votes")
    message: Optional[Message] = Relationship(back_populates="votes")


# ===== 建议模型 =====
class SuggestionBase(SQLModel):
    original_text: str
    suggested_text: str
    description: Optional[str] = None
    is_resolved: bool = Field(default=False)


class Suggestion(SuggestionBase, table=True):
    __tablename__ = "Suggestion"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="Document.id", nullable=False)
    document_created_at: datetime = Field(foreign_key="Document.created_at", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="User.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships
    user: Optional[User] = Relationship(back_populates="suggestions")


# ===== 小红书分享模型 =====
class XhsShareRequest(SQLModel):
    type: str
    title: str = Field(min_length=1, max_length=60)
    content: str = Field(min_length=1, max_length=2000)
    images: Optional[List[str]] = None
    video: Optional[str] = None
    cover: Optional[str] = None


class XhsShareResponse(SQLModel):
    success: bool
    shareInfo: Dict[str, Any]
