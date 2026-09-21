"""SDK exceptions."""


class WebsiteAuditLeadsError(RuntimeError):
    """Base SDK exception."""


class AuthenticationError(WebsiteAuditLeadsError):
    """Apify token is missing or rejected."""


class ActorRunError(WebsiteAuditLeadsError):
    """Actor run or result retrieval failed."""


class ActorTimeoutError(WebsiteAuditLeadsError):
    """Actor run did not finish within the client timeout."""
