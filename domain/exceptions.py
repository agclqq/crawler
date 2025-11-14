"""领域异常定义"""


class DomainError(Exception):
    """领域基础异常"""

    pass


class InvalidURLError(DomainError):
    """无效 URL 异常"""

    pass


class TaskNotFoundError(DomainError):
    """任务未找到异常"""

    pass


class TaskStateError(DomainError):
    """任务状态错误异常"""

    pass
