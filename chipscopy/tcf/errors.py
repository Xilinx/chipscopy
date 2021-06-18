# *****************************************************************************
# * Copyright (c) 2011, 2013-2014, 2016 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

import time

# Error report attribute names

ERROR_CODE = "Code"
"""Integer : error code value"""

ERROR_TIME = "Time"
"""Integer : error time"""

ERROR_SERVICE = "Service"
"""String : name of the service the error occured in"""

ERROR_FORMAT = "Format"
"""String : error format"""

ERROR_PARAMS = "Params"
"""List : a list of parameters for the given error"""

ERROR_SEVERITY = "Severity"
"""Integer : error severity"""

ERROR_ALT_CODE = "AltCode"
"""Integer : error alternative code value"""

ERROR_ALT_ORG = "AltOrg"
"""Integer : error alternative org???"""

ERROR_CAUSED_BY = "CausedBy"
"""Object : the cause of the error"""

# Error severity codes
SEVERITY_ERROR = 0
"""Error"""

SEVERITY_WARNING = 1
"""Warning"""

SEVERITY_FATAL = 2
"""Fatal error"""

# Error code ranges
# Standard TCF code range
CODE_STD_MIN = 0
"""Minimum error code value"""
CODE_STD_MAX = 0xffff
"""Maximum error code value"""

# Service specific codes. Decoding requires service ID.
CODE_SERVICE_SPECIFIC_MIN = 0x10000
"""Service specific minimum error code value"""
CODE_SERVICE_SPECIFIC_MAX = 0x1ffff
"""Service specific maximum error code value"""

# Reserved codes - will never be used by the TCF standard
CODE_RESERVED_MIN = 0x20000
"""Service specific reserved minimum error code value"""
CODE_RESERVED_MAX = 0x2ffff
"""Service specific reserved maximum error code value"""

# Standard TCF error codes
TCF_ERROR_OTHER = 1
"""Other TCF errors"""

TCF_ERROR_JSON_SYNTAX = 2
"""JSON syntax error"""

TCF_ERROR_PROTOCOL = 3
"""Protocol error"""

TCF_ERROR_BUFFER_OVERFLOW = 4
"""Buffer overflow"""

TCF_ERROR_CHANNEL_CLOSED = 5
"""Channel closed"""

TCF_ERROR_COMMAND_CANCELLED = 6
"""Command canceled"""

TCF_ERROR_UNKNOWN_PEER = 7
"""Unknown peer"""

TCF_ERROR_BASE64 = 8
"""Base64 error"""

TCF_ERROR_EOF = 9
"""End of file"""

TCF_ERROR_ALREADY_STOPPED = 10
"""Already stopped"""

TCF_ERROR_ALREADY_EXITED = 11
"""Already exited"""

TCF_ERROR_ALREADY_RUNNING = 12
"""Already running"""

TCF_ERROR_ALREADY_ATTACHED = 13
"""Already attached"""

TCF_ERROR_IS_RUNNING = 14
"""Is running"""

TCF_ERROR_INV_DATA_SIZE = 15
"""Invalid data size"""

TCF_ERROR_INV_CONTEXT = 16
"""Invalid context"""

TCF_ERROR_INV_ADDRESS = 17
"""Invalid address"""

TCF_ERROR_INV_EXPRESSION = 18
"""Invalid expression"""

TCF_ERROR_INV_FORMAT = 19
"""Invalid format"""

TCF_ERROR_INV_NUMBER = 20
"""Invalid number"""

TCF_ERROR_INV_DWARF = 21
"""Invalid dwarf"""

TCF_ERROR_SYM_NOT_FOUND = 22
"""Symbol not found"""

TCF_ERROR_UNSUPPORTED = 23
"""Unsupported"""

TCF_ERROR_INV_DATA_TYPE = 24
"""Invalid data type"""

TCF_ERROR_INV_COMMAND = 25
"""Invalid command"""

TCF_ERROR_INV_TRANSPORT = 26
"""Invalid transport"""

TCF_ERROR_CACHE_MISS = 27
"""Cache miss"""

TCF_ERROR_NOT_ACTIVE = 28
"""Not active"""

_timestamp_format = "%Y-%m-%d %H:%M:%S"


class ErrorReport(Exception):
    """TCF error report class.

    :param msg: error report message
    :param attrs: TCF error report attributes to initialise this error report
                  with. See **ERROR_***.
    """
    def __init__(self, msg, attrs):
        super(ErrorReport, self).__init__(msg)
        if isinstance(attrs, int):
            attrs = {
                ERROR_CODE: attrs,
                ERROR_TIME: int(time.time() * 1000),
                ERROR_FORMAT: msg,
                ERROR_SEVERITY: SEVERITY_ERROR
            }
        self.attrs = attrs
        caused_by = attrs.get(ERROR_CAUSED_BY)
        if caused_by:
            errMap = caused_by
            bf = 'TCF error report:\n'
            bf += appendErrorProps(errMap)
            self.caused_by = ErrorReport(bf, errMap)

    def getErrorCode(self):
        """Get this exception error code.

        :returns: This error report error code, or **0**
        """
        return self.attrs.get(ERROR_CODE) or 0

    def getAltCode(self):
        """Get this exception alternative error code.

        :returns: This error report alternative error code, or **0**
        """
        return self.attrs.get(ERROR_ALT_CODE) or 0

    def getAltOrg(self):
        """Get this exception alternative org ???

        :returns: This error report alernative org???, or **None**
        """
        return self.attrs.get(ERROR_ALT_ORG)

    def getAttributes(self):
        """Get this error attribute.

        :returns: a :class:`dict` of this error attributes
        """
        return self.attrs


def toErrorString(data):
    if not data:
        return None
    errMap = data
    fmt = errMap.get(ERROR_FORMAT)
    if fmt:
        c = errMap.get(ERROR_PARAMS)
        if c:
            return fmt.format(c)
        return fmt
    code = errMap.get(ERROR_CODE)
    if code is not None:
        if code == TCF_ERROR_OTHER:
            alt_org = errMap.get(ERROR_ALT_ORG)
            alt_code = errMap.get(ERROR_ALT_CODE)
            if alt_org and alt_code:
                return "%s Error %d" % (alt_org, alt_code)
        return "TCF Error %d" % code
    return "Invalid error report format"


def appendErrorProps(errMap):
    timeVal = errMap.get(ERROR_TIME)
    code = errMap.get(ERROR_CODE)
    service = errMap.get(ERROR_SERVICE)
    severity = errMap.get(ERROR_SEVERITY)
    alt_code = errMap.get(ERROR_ALT_CODE)
    alt_org = errMap.get(ERROR_ALT_ORG)
    bf = ''
    if timeVal:
        bf += '\nTime: '
        bf += time.strftime(_timestamp_format, time.localtime(timeVal / 1000.))
    if severity:
        bf += '\nSeverity: '
        if severity == SEVERITY_ERROR:
            bf += 'Error'
        elif severity == SEVERITY_FATAL:
            bf += 'Fatal'
        elif severity == SEVERITY_WARNING:
            bf += 'Warning'
        else:
            bf += 'Unknown'
    bf += '\nError text: ' + str(toErrorString(errMap)) + '\n'
    bf += 'Error code: ' + str(code)
    if service:
        bf += '\nService: ' + str(service)
    if alt_code:
        bf += '\nAlt code: ' + str(alt_code)
        if alt_org:
            bf += '\nAlt org: ' + str(alt_org)
    return bf
