class common:
    agent_name = "top_header"
    agent_description = "This section is present on top of the search result page which includes the journey details, navigate back to previous home page and an option to modify journey details"

class mweb(common):
    pass

class dweb(common):
    agent_name = "top_header"
    agent_description = "This section is present on top of the search result page (below line of business selection like bus, ferry, etc) which includes the source and destination details, navigate back to previous home page and options to modify journey details. If journey details need modification, use this instead of going back to home page (unless explicitly specified)"

class android(common):
    pass

class ios(common):
    pass

