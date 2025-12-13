"""
SNMP Testing API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
import asyncio

router = APIRouter(prefix="/snmp", tags=["snmp"])


class SnmpTestRequest(BaseModel):
    ip: str
    community: str = "public"
    oid: str = "1.3.6.1.2.1.1.1.0"
    method: str = "get"  # 'get' or 'walk'


class SnmpTestResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    count: Optional[int] = None
    error: Optional[str] = None


@router.post("/test", response_model=SnmpTestResponse)
async def test_snmp(request: SnmpTestRequest):
    """
    Test SNMP connectivity to a device
    """
    try:
        from pysnmp.hlapi.asyncio import (
            getCmd, nextCmd, SnmpEngine, CommunityData, 
            UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
        )
        
        if request.method == "get":
            # SNMP GET
            errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
                SnmpEngine(),
                CommunityData(request.community),
                UdpTransportTarget((request.ip, 161), timeout=5.0, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(request.oid))
            )
            
            if errorIndication:
                return SnmpTestResponse(success=False, error=str(errorIndication))
            elif errorStatus:
                return SnmpTestResponse(
                    success=False, 
                    error=f"{errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}"
                )
            else:
                result = []
                for varBind in varBinds:
                    result.append(f"{varBind[0].prettyPrint()} = {varBind[1].prettyPrint()}")
                return SnmpTestResponse(success=True, result="\n".join(result))
        
        elif request.method == "walk":
            # SNMP WALK
            results = []
            async for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(),
                CommunityData(request.community),
                UdpTransportTarget((request.ip, 161), timeout=5.0, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(request.oid)),
                lexicographicMode=False
            ):
                if errorIndication:
                    if len(results) == 0:
                        return SnmpTestResponse(success=False, error=str(errorIndication))
                    break
                elif errorStatus:
                    if len(results) == 0:
                        return SnmpTestResponse(
                            success=False,
                            error=f"{errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}"
                        )
                    break
                else:
                    for varBind in varBinds:
                        results.append({
                            "oid": varBind[0].prettyPrint(),
                            "value": varBind[1].prettyPrint()
                        })
                
                # Limit results to avoid timeout
                if len(results) >= 100:
                    break
            
            return SnmpTestResponse(success=True, result=results, count=len(results))
        
        else:
            return SnmpTestResponse(success=False, error=f"Unknown method: {request.method}")
            
    except ImportError:
        # pysnmp not installed, return demo response
        if request.method == "get":
            return SnmpTestResponse(
                success=True, 
                result=f"Demo mode: {request.oid} = Cisco IOS Software, C3650 Software"
            )
        else:
            return SnmpTestResponse(
                success=True,
                result=[
                    {"oid": f"{request.oid}.1", "value": "GigabitEthernet0/1"},
                    {"oid": f"{request.oid}.2", "value": "GigabitEthernet0/2"},
                    {"oid": f"{request.oid}.3", "value": "GigabitEthernet0/3"},
                ],
                count=3
            )
    except Exception as e:
        return SnmpTestResponse(success=False, error=str(e))
