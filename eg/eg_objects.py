class User():
    """
    Object representation of a participant in the database.
    """
    
    # Status codes
    ALLOCATED = 1
    CONSENTED = 2
    ASSESSED = 3
    INSTRUCTED = 4
    
    id = 0
    username = ""
    password = ""
    #worker = relationship("Participant",backref="user",cascade="all,delete")
    lastvisit = None
    sessionId = ""
    status = 1
    datastring = ""
    email = ""
    ipaddress = ""
    ip_in_use= ""
    note =  ""
    #codes = relationship("Code",backref="user",cascade="all,delete")
    
    def __init__(self):
        pass
    
    def __repr__( self ):
        return "Subject(%s, %s, %r, %r, %s)" % ( 
            self.assignmentId, 
            self.workerId, 
            self.cond, 
            self.status,
            self.codeversion )

#Index('idx_worker_in_user', User.worker)