#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Name: UseOfPythonDemo_gRPC_reflection.py
Description: The script uses gRPC with a subscription based approach to read data consistently from the RT environment of the PLCnext Engineer project.
             It reads two boolean values, performs a logic AND operation on them and writes the result to a third variable in the RT execution task.
             Additionally, a second variable is toggled and written to the PLCnext project on every cycle to track execution of the script. 
 
Author: Pedro Aguilar
Compatibility :     grpcio = 1.76.0
                    grpcio-reflection = 1.76.0
Created: 2026-02-12
Version: 1.0
License: No-License

Helping tips:

1. The Port Data Types info can be seen in the protobuf generated file: "gRPC-master/pxc_grpc/ArpTypes_pb2.py". 
   That file is only available when using GRPC not with reflection but with the protobuf files.
   Alternatively, the list is shown in the old post from 2022: https://www.plcnext-community.net/makersblog/grpc-python-read-and-write-process-data/

2. More information on what can be done with the GRPC can be infered from the api documentation: https://api.plcnext.help/

3. NOTICE! that the channel is insecure and the API allows for controlling the device remotely. Misuse can lead to a security risk. 

"""

import grpc
from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase
from google.protobuf.descriptor_pool import DescriptorPool
from google.protobuf.descriptor import FieldDescriptor
from google.protobuf import message_factory
import time
import os

# ---------------------------------------------------------------------------------------
# Function to perform the gRPC call. 
# ---------------------------------------------------------------------------------------

def call_gRPC ( method_full_name, request, serialized_request, responseClass, print_debug = False):
    try:
        response = channel.unary_unary(
            method_full_name,
            request_serializer=lambda _: serialized_request,
            response_deserializer=responseClass.FromString
        )(request)
        if print_debug:
            print("gRPC call executed!")
            print("\nResponse message received:")
            print(response)
            print("\nFields of the response message:")
            for field in response.DESCRIPTOR.fields:
                value = getattr(response, field.name)
                print(f"{field.name}: {value}")
        else:
            pass
        return response
    except grpc.RpcError as e:
        print(f"\ngRPC error: {e.code()} - {e.details()}")
        
# ---------------------------------------------------------------------------------------
# Function to explore the structures and data types handled by the methods 
# (useful when debugging/passing data for the first time)
# ---------------------------------------------------------------------------------------

def get_mth_desc (service_name, method_name, print_debug = False):
    try:
        service_descriptor = desc_pool.FindServiceByName(service_name)  # Get the service structure
        method_descriptor = service_descriptor.FindMethodByName(method_name)   # Get the method structure
        req_desc = method_descriptor.input_type
        if print_debug:
            print("Method Description:", req_desc.full_name)
            for field in req_desc.fields:
                print(f"Field: {field.name}, Type: {field.type}")
                if field.type == FieldDescriptor.TYPE_ENUM:
                    enum_desc = field.enum_type
                    print("\nFound ENUM:", enum_desc.full_name)
                    print("Values:")
                    for v in enum_desc.values:
                        print(f"  {v.name} = {v.number}")
    except KeyError as e:
        print(f"Error: {e}")
        exit(1)
    return method_descriptor

# ---------------------------------------------------------------------------------------
# Function to alternate the heartbeat state
# ---------------------------------------------------------------------------------------

def heartbeat (debug_HeartbeatVar):
    if debug_HeartbeatVar == '     _♡_     ':
        debug_HeartbeatVar = '     «♥»     '
    else: 
        debug_HeartbeatVar = '     _♡_     '
    return debug_HeartbeatVar


# ---------------------------------------------------------------------------------------
# List of variables to read/write: 
# The Data Types come from the protobuf generated file: gRPC-master/pxc_grpc/ArpTypes_pb2.py
# That file is only available when using GRPC not with reflection but with the protobuf files. 
# ---------------------------------------------------------------------------------------

''' Helper Data types CT [Core Type (?)] for GRPC comm upon data receival or direct writing.
CT_None = 0
CT_End = 0
CT_Void = 1
CT_Boolean = 2
CT_Char = 3
CT_Int8 = 4
CT_Uint8 = 5
CT_Int16 = 6
CT_Uint16 = 7
CT_Int32 = 8
CT_Uint32 = 9
CT_Int64 = 10
CT_Uint64 = 11
CT_Real32 = 12
CT_Real64 = 13
CT_Struct = 18
CT_String = 19
CT_Utf8String = 19
CT_Array = 20
CT_DateTime = 23
CT_Version = 24
CT_Guid = 25
CT_AnsiString = 26
CT_Object = 28
CT_Utf16String = 30
CT_Stream = 34
CT_Enumerator = 35
CT_SecureString = 36
CT_Enum = 37
CT_Dictionary = 38
CT_SecurityToken = 39
CT_Exception = 40
CT_IecTime = 41
CT_IecTime64 = 42
CT_IecDate = 43
CT_IecDate64 = 44
CT_IecDateTime = 45
CT_IecDateTime64 = 46
CT_IecTimeOfDay = 47
CT_IecTimeOfDay64 = 48
'''

# ---------------------------------------------------------------------------------------
# List of variables to read from the controller [gds_address, dtype]
# ---------------------------------------------------------------------------------------

variablelist_toread = [
    ["Arp.Plc.Eclr/Py_AND_xInputA"   , 19],
    ["Arp.Plc.Eclr/Py_AND_xInputB"   , 19],
    ]
# Extract the GDS addresses of the variables
listofvariables_toread = [column[0] for column in variablelist_toread[0:]]


# ---------------------------------------------------------------------------------------
# List of variables to write to the controller [gds_address, dtype, placeholder_value]
# ---------------------------------------------------------------------------------------

variablelist_towrite = [
    ["Arp.Plc.Eclr/Py_AND_xResult"       , 2 ,   ""],
    ["Arp.Plc.Eclr/Py_strHBVar"     , 19,   "     -♡-     "],
]

# Extract the GDS addresses of the variables
listofvariables_towrite = [column[0] for column in variablelist_towrite[0:]]

# Extract the data types the variables
listofdatatypes_towrite = [column[1] for column in variablelist_towrite[0:]]

# Extract the placeholder (dummy values) of the variables
listofdata_towrite = [column[2] for column in variablelist_towrite[0:]]

# ---------------------------------------------------------------------------------------
# Socket connection configuration for the PLCnext gRPC server
# ---------------------------------------------------------------------------------------
channel = grpc.insecure_channel("unix:/run/plcnext/grpc.sock")

reflection_db = ProtoReflectionDescriptorDatabase(channel)
desc_pool = DescriptorPool(reflection_db)

# ---------------------------------------------------------------------------------------
# Step 1: Create a subscription service to get a subscription ID
# ---------------------------------------------------------------------------------------
subscription_service_name = "Arp.Plc.Gds.Services.Grpc.ISubscriptionService"                        # Required service from the pool
create_subs_method = "CreateSubscription"                                                           # Required method from the service

create_subs_method_desc = get_mth_desc (subscription_service_name, create_subs_method)              # Get method descriptor
subscribing_method_full_name = f"/{subscription_service_name}/{create_subs_method}"                 # Method full name for creating/getting a subscription ID

RequestClassSubscriptionID = message_factory.GetMessageClass(create_subs_method_desc.input_type)    # Dynamic request message class to get a Subscription ID 
ResponseClassSubscriptionID = message_factory.GetMessageClass(create_subs_method_desc.output_type)  # Dynamic response message class to get the Subscription ID

create_subs_req = RequestClassSubscriptionID()
create_subs_req.kind = 1                                                                            # Type of subscription desired (1 = HighPerformance) --> check api documentation or method structure for more info)

create_subs_req_serialized = create_subs_req.SerializeToString()
create_subs_resp = call_gRPC (subscribing_method_full_name, create_subs_req, create_subs_req_serialized, ResponseClassSubscriptionID)

subsID = create_subs_resp._ReturnValue
print(f"The subscription ID to use is: {subsID}")

# ---------------------------------------------------------------------------------------
# Step 2: Associate the variables that are going to be read via the subscription
# ---------------------------------------------------------------------------------------

addvartosubs_method = "AddVariables"                                                                # Required method from the service
addvartosubs_method_desc = get_mth_desc (subscription_service_name, addvartosubs_method)            # Get method descriptor
addvarstosubs_method_full_name = f"/{subscription_service_name}/{addvartosubs_method}"              # Method full name for adding variables to the desired subscription

RequestClassAddvarstosub = message_factory.GetMessageClass(addvartosubs_method_desc.input_type)     # Dynamic request message class to pass the list of variables to subscribe to. 
ResponseClassAddvarstosub = message_factory.GetMessageClass(addvartosubs_method_desc.output_type)   # Dynamic response message class to get confirmation of the association 

addvarstosub_request = RequestClassAddvarstosub ()
addvarstosub_request.subscriptionId = subsID                                                        # subscription ID obtained before
addvarstosub_request.variableNames.extend(listofvariables_toread)                                   # Variable that will be subscribed to. 

print(f"List of variables to read using the Subscription ID '{subsID}':")
print(listofvariables_toread)

addvarstosub_serialized_request = addvarstosub_request.SerializeToString()
addvarstosub_request_response = call_gRPC ( addvarstosubs_method_full_name, addvarstosub_request, addvarstosub_serialized_request, ResponseClassAddvarstosub) 

print(f"\nThe list of variables was passed to the gRPC server and it returned: {addvarstosub_request_response}") # "DAE_None" means succesfull



# ---------------------------------------------------------------------------------------
# Step 3: Activate the subscription
# ---------------------------------------------------------------------------------------

subscribe_method = "Subscribe"
subscribe_method_desc = get_mth_desc(subscription_service_name, subscribe_method)
subscribe_method_full_name = f"/{subscription_service_name}/{subscribe_method}"             # Method full name for creating the subscription with a given SubsID and a list of variab

RequestClassSubscribe = message_factory.GetMessageClass(subscribe_method_desc.input_type)
ResponseClassSubscribe = message_factory.GetMessageClass(subscribe_method_desc.output_type)

subscribe_request = RequestClassSubscribe ()
subscribe_request.subscriptionId = subsID                                     # subscription ID obtained before
subscribe_request.sampleRate = 100000                                              # Sample rate in microseconds, 0 in this case for global variables means 50ms

subscribe_serialized_request = subscribe_request.SerializeToString()
subscribe_request_response = call_gRPC ( subscribe_method_full_name, subscribe_request, subscribe_serialized_request, ResponseClassSubscribe)


print(f"The subscription was initializated/actiaved and the server returned: {subscribe_request_response}") # The response DAE_None means succesfull. 

# ---------------------------------------------------------------------------------------
# Step 4: Build the structures for reading data from the subscription
# ---------------------------------------------------------------------------------------

readValues_method = "ReadValues"
readValues_method_desc = get_mth_desc ( subscription_service_name, readValues_method)
readValues_method_full_name = f"/{subscription_service_name}/{readValues_method}"           # Method full name for reading the values of the subscribed variables.

RequestClassReadValues = message_factory.GetMessageClass(readValues_method_desc.input_type)
ResponseClassReadValues = message_factory.GetMessageClass(readValues_method_desc.output_type)

readValues_request = RequestClassReadValues ()
readValues_request.subscriptionId = subsID                                     # subscription ID obtained before

readValues_serialized_request = readValues_request.SerializeToString()

# ==> NOTICE: Since the reading will be performed cyclically then the grpc call is not made here but in the main loop of the program. 


# ---------------------------------------------------------------------------------------
# Step 5: Build the structures for writing data to the GDS [this happens without subscription]
# Note: Alternatively, a direct read from the GDS can be executed (shown below, but data consistency is not guaranteed)
# ---------------------------------------------------------------------------------------

dataAccess_service_name = "Arp.Plc.Gds.Services.Grpc.IDataAccessService" 
write_method_name = "Write"

write_method_desc = get_mth_desc (dataAccess_service_name, write_method_name)
writing_method_full_name = f"/{dataAccess_service_name}/{write_method_name}"

RequestClasswrite = message_factory.GetMessageClass(write_method_desc.input_type)
ResponseClasswrite = message_factory.GetMessageClass(write_method_desc.output_type)

# ---------------------------------------------------------------------------------------
# Execute reading and updating cyclically 
# ---------------------------------------------------------------------------------------

print('Script execution starting!')
while True:
    # read_response = call_gRPC ( reading_method_full_name, reading_request, reading_serialized_request, ResponseClassread)
    read_response = call_gRPC ( readValues_method_full_name, readValues_request, readValues_serialized_request, ResponseClassReadValues)
    listofvariablesread = []

    for i in range(len(read_response.values)):
        value = read_response.values[i]
        var_name = listofvariables_toread[i]
        # Extract the right value type based on TypeCode
        if value.HasField("StringValue"):
            read_val = value.StringValue
        elif value.HasField("Int16Value"):
            read_val = value.Int16Value
        elif value.HasField("FloatValue"):
            read_val = value.FloatValue
        elif value.HasField("BoolValue"):
            read_val = value.BoolValue
        else:
            read_val = "<unsupported type>"
        listofvariablesread.append((var_name, read_val))

    # ---------------------------------------------------------------------------------------
    # Perform the logic AND operation. 
    # ---------------------------------------------------------------------------------------

    andresult = bool(listofvariablesread[0][1]) and bool(listofvariablesread [1][1])
    # print(f'The result of the and operation is: {andresult}') 

    #Updating the data to write with the result
    variablelist_towrite[0][2] = andresult
    
    # Updating heartbeat variable
    variablelist_towrite[1][2] = heartbeat(variablelist_towrite[1][2])

    # ---------------------------------------------------------------------------------------
    # Build the writing request
    # ---------------------------------------------------------------------------------------
    writingrequest = RequestClasswrite()

    for port, typecode, write_value in variablelist_towrite:
        dataitem = writingrequest.data.add()  # Creates a data item instance
        dataitem.PortName = port
        dataitem.Value.TypeCode = typecode
        value = dataitem.Value  # This is the nested message (automatically created)
        # Set the appropriate field based on type code
        if typecode == 19:  # CT_String
            dataitem.Value.StringValue = write_value
        elif typecode == 6:  # CT_Int16
            dataitem.Value.Int16Value = write_value
        elif typecode == 12:  # CT_Real32
            dataitem.Value.FloatValue = write_value
        elif typecode == 2:  # CT_Boolean
            dataitem.Value.BoolValue = write_value
        else:
            pass

    writing_serialized_request = writingrequest.SerializeToString()

    call_gRPC ( writing_method_full_name, writingrequest, writing_serialized_request, ResponseClasswrite)
    # os.system("clear")
    # print("Working!")
    time.sleep(0.1)
