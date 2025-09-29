import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import AnyUrl, EmailStr, field_validator
from sqlmodel import JSON, Column, Field, Relationship, SQLModel


def utc_now():
    return datetime.now(UTC)


# ===== 枚举定义 =====
class UserType(str, Enum):
    GUEST = "guest"
    REGULAR = "regular"


class ChatModelId(str, Enum):
    CHAT_MODEL = "chat-model"
    CHAT_MODEL_REASONING = "chat-model-reasoning"


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
    password: str | None = Field(default=None, max_length=64)
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
    documents: list["Document"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    suggestions: list["Suggestion"] = Relationship(
        back_populates="user", cascade_delete=True
    )


class UserPublic(UserBase):
    id: str
    
    @classmethod
    def from_user(cls, user: User) -> "UserPublic":
        """从User对象创建UserPublic对象"""
        return cls(
            id=str(user.id),
            email=user.email,
            is_active=user.is_active
        )


# ===== 聊天模型 =====
class ChatBase(SQLModel):
    title: str = Field(max_length=255)
    visibility: Visibility = Field(default=Visibility.PRIVATE)


class ChatCreate(ChatBase):
    pass


class Chat(ChatBase, table=True):
    __tablename__ = "Chat"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="User.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=utc_now)
    last_context: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    # Relationships
    user: User | None = Relationship(back_populates="chats")
    messages: list["Message"] = Relationship(back_populates="chat", cascade_delete=True)
    votes: list["Vote"] = Relationship(back_populates="chat", cascade_delete=True)


class ChatPublic(ChatBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


# ===== 消息模型 =====
class MessageBase(SQLModel):
    role: MessageRole
    parts: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    attachments: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )


class MessageCreate(MessageBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

    @field_validator("role", mode="before")
    @classmethod
    def validate_role_is_user(cls, value: Any) -> MessageRole:
        """确保聊天请求只提交用户消息。"""

        # 处理字符串输入
        if isinstance(value, str):
            if value == "user":
                return MessageRole.USER
            else:
                raise ValueError("Only user messages can be submitted to the chat API.")
        # 处理枚举值输入
        if value != MessageRole.USER:
            raise ValueError("Only user messages can be submitted to the chat API.")
        return value

    @field_validator("parts", mode="before")
    @classmethod
    def validate_parts(cls, value: Any) -> list[dict[str, Any]]:
        """校验消息片段结构，与NextJS版本保持一致。"""

        if not isinstance(value, list) or not value:
            raise ValueError("Message parts must be a non-empty list.")

        validated: list[dict[str, Any]] = []
        for index, part in enumerate(value):
            if not isinstance(part, dict):
                raise ValueError("Each message part must be an object.")

            part_type = part.get("type")
            if part_type == "text":
                text = part.get("text")
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(
                        "Text parts must include a non-empty string field 'text'."
                    )
                if len(text) > 2000:
                    raise ValueError("Text parts cannot exceed 2000 characters.")
                validated.append({"type": "text", "text": text})
                continue

            if part_type == "file":
                media_type = part.get("mediaType")
                name = part.get("name")
                url = part.get("url")
                if media_type not in {"image/jpeg", "image/png"}:
                    raise ValueError("File parts must declare a supported mediaType.")
                if not isinstance(name, str) or not name.strip() or len(name) > 100:
                    raise ValueError(
                        "File parts must include a filename up to 100 characters."
                    )
                if not isinstance(url, str) or not url:
                    raise ValueError("File parts must include a valid url string.")
                validated.append(
                    {
                        "type": "file",
                        "mediaType": media_type,
                        "name": name,
                        "url": url,
                    }
                )
                continue

            raise ValueError(f"Unsupported message part type at index {index}.")

        return validated


class Message(MessageBase, table=True):
    __tablename__ = "Message_v2"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    chat_id: uuid.UUID = Field(
        foreign_key="Chat.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships
    chat: Chat | None = Relationship(back_populates="messages")
    votes: list["Vote"] = Relationship(back_populates="message", cascade_delete=True)


class MessagePublic(MessageBase):
    id: uuid.UUID
    chat_id: uuid.UUID
    created_at: datetime


# ===== 聊天请求模型 =====
class ChatRequest(SQLModel):
    id: uuid.UUID
    message: MessageCreate
    selectedChatModel: ChatModelId = ChatModelId.CHAT_MODEL
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
    sub: str | None = None
    type: str | None = None


# ===== AI工具模型 =====
class ImageGenerationRequest(SQLModel):
    prompt: str = Field(description="图片描述文本")
    style: str = "realistic"  # realistic, artistic, cartoon, abstract
    size: str = "1024x1024"  # 512x512, 768x768, 1024x1024


class ImageGenerationResponse(SQLModel):
    result: dict[str, Any]
    prompt: str
    style: str
    size: str


class ContentRewriteRequest(SQLModel):
    originalContent: str = Field(description="原始内容")
    rewriteType: str = "improve_clarity"  # improve_clarity, make_professional, etc.
    targetTone: str | None = None  # professional, casual, friendly, etc.
    targetAudience: str | None = None
    additionalInstructions: str | None = None


class ContentRewriteResponse(SQLModel):
    success: bool
    originalContent: str
    rewrittenContent: str
    rewriteType: str
    targetTone: str | None = None
    targetAudience: str | None = None
    originalLength: int
    rewrittenLength: int


# ===== 文件上传模型 =====
class FileUploadResponse(SQLModel):
    url: str
    pathname: str
    contentType: str
    size: int
    uploadedAt: datetime


# ===== 文档模型 =====
class DocumentKind(str, Enum):
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    SHEET = "sheet"


class DocumentBase(SQLModel):
    title: str
    content: str | None = None
    kind: DocumentKind = Field(default=DocumentKind.TEXT)


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    title: str | None = None
    content: str | None = None
    kind: DocumentKind | None = None


class Document(DocumentBase, table=True):
    __tablename__ = "Document"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="User.id", nullable=False, ondelete="CASCADE"
    )

    # Relationships
    user: User | None = Relationship(back_populates="documents")


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
    chat: Chat | None = Relationship(back_populates="votes")
    message: Message | None = Relationship(back_populates="votes")


# ===== 建议模型 =====
class SuggestionBase(SQLModel):
    original_text: str
    suggested_text: str
    description: str | None = None
    is_resolved: bool = Field(default=False)


class Suggestion(SuggestionBase, table=True):
    __tablename__ = "Suggestion"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="Document.id", nullable=False)
    document_created_at: datetime = Field(
        foreign_key="Document.created_at", nullable=False
    )
    user_id: uuid.UUID = Field(
        foreign_key="User.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships
    user: User | None = Relationship(back_populates="suggestions")


# ===== 小红书分享模型 =====
class XhsShareRequest(SQLModel):
    type: Literal["normal", "video"]
    title: str = Field(min_length=1, max_length=60)
    content: str = Field(min_length=1, max_length=2000)
    images: list[AnyUrl] | None = None
    video: AnyUrl | None = None
    cover: AnyUrl | None = None
    url: AnyUrl


class XhsShareResponse(SQLModel):
    shareInfo: dict[str, Any]
    verifyConfig: dict[str, str]
