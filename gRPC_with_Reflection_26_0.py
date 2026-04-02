
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Name: gRPC_with_Reflection_26_0.py

Version 26.0: The script writes first data to each variable in the MainInstance programm running on the PLC as per the Table "variablelist_towrite". After that, 
              it requests the values of the same variables from the PLC using the table "variablelist" and displays that in the console before finishing execution. 
 
Author: Pedro Aguilar
Compatibility tested with :     grpcio = 1.76.0
                                grpcio-reflection = 1.76.0
Created: 2026-02-12
Version: 26.0
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

# List of variables to be read (port, data type)
variablelist = [
    ("Arp.Plc.Eclr/MainInstance.strInput"   , 19),
    ("Arp.Plc.Eclr/MainInstance.str1"       , 19),
    ("Arp.Plc.Eclr/MainInstance.i1"         , 6),
    ("Arp.Plc.Eclr/MainInstance.iInput"     , 6),
    ("Arp.Plc.Eclr/MainInstance.rInput"     , 12),
    ("Arp.Plc.Eclr/MainInstance.r1"         , 12),
    ("Arp.Plc.Eclr/MainInstance.xOutput"    , 2),
    ("Arp.Plc.Eclr/MainInstance.x1"         , 2),
    ("Arp.Plc.Eclr/MainInstance.xInput"     , 2),
    ("Arp.Plc.Eclr/MainInstance.x2"         , 2),
    ("Arp.Plc.Eclr/MainInstance.strInput2"  , 19),
    ("Arp.Plc.Eclr/MainInstance.str2"       , 19),
]

# Getting each column separately
listofvariables = [column[0] for column in variablelist[0:]]

# List of variables to be written (port, data type, data_to_be_written)
variablelist_towrite = [
    ("Arp.Plc.Eclr/MainInstance.strInput"   , 19,   "Testing"),
    ("Arp.Plc.Eclr/MainInstance.str1"       , 19,   "Write to multiple variables"),
    ("Arp.Plc.Eclr/MainInstance.i1"         , 6,    18),
    ("Arp.Plc.Eclr/MainInstance.iInput"     , 6,    23),
    ("Arp.Plc.Eclr/MainInstance.rInput"     , 12,   32.5),
    ("Arp.Plc.Eclr/MainInstance.r1"         , 12,   54.7),
    ("Arp.Plc.Eclr/MainInstance.xOutput"    , 2,    "True"),
    ("Arp.Plc.Eclr/MainInstance.x1"         , 2,    "True"),
    ("Arp.Plc.Eclr/MainInstance.xInput"     , 2,    "False"),
    ("Arp.Plc.Eclr/MainInstance.x2"         , 2,    "False"),
    ("Arp.Plc.Eclr/MainInstance.strInput2"  , 19,   "And ..."),
    ("Arp.Plc.Eclr/MainInstance.str2"       , 19,   "It works now?"),
]

# ---------------------------------------------------------------------------------------
# Connect to gRPC server
# ---------------------------------------------------------------------------------------
channel = grpc.insecure_channel("unix:/run/plcnext/grpc.sock")

# ---------------------------------------------------------------------------------------
# Setting up the reflection database for the methods and services of the server.
# ---------------------------------------------------------------------------------------
reflection_db = ProtoReflectionDescriptorDatabase(channel)
desc_pool = DescriptorPool(reflection_db)

# ---------------------------------------------------------------------------------------
# Defining the service and methods to be used for reading and writing data.
# ---------------------------------------------------------------------------------------
service_name = "Arp.Plc.Gds.Services.Grpc.IDataAccessService"
method_name = "Read"

# service_name_towrite = "Arp.Plc.Gds.Services.Grpc.IDataAccessService"
method_name_towrite = "Write"

# ---------------------------------------------------------------------------------------
# Look up the service and method descriptors from within the whole set
# ---------------------------------------------------------------------------------------
try:
    service_desc        = desc_pool.FindServiceByName(service_name)
    method_desc         = service_desc.FindMethodByName(method_name)
    write_method_desc = service_desc.FindMethodByName(method_name_towrite)
except KeyError as e:
    print(f"Error: {e}")
    exit(1)

# ---------------------------------------------------------------------------------------
# Get dynamic message classes for request to and response from the server (for reading).
# ---------------------------------------------------------------------------------------

RequestClass = message_factory.GetMessageClass(method_desc.input_type)    
ResponseClass = message_factory.GetMessageClass(method_desc.output_type)  

# ---------------------------------------------------------------------------------------
# Get dynamic message classes for request to and response from the server (for writing).
# ---------------------------------------------------------------------------------------
RequestClasswrite = message_factory.GetMessageClass(write_method_desc.input_type)
ResponseClasswrite = message_factory.GetMessageClass(write_method_desc.output_type)

# ---------------------------------------------------------------------------------------
# Create and populate the request for writing
# ---------------------------------------------------------------------------------------
requestwrite = RequestClasswrite()

# ---------------------------------------------------------------------------------------
# Create and populate from the variable list, the dataitem to pass to the server. 
# ---------------------------------------------------------------------------------------

for port, typecode, write_value in variablelist_towrite:
    dataitem = requestwrite.data.add()  # Creates a data item instance
    dataitem.PortName = port
    dataitem.Value.TypeCode = typecode
    value = dataitem.Value  # This is the nested message (automatically created)
    # Settting the appropriate field based on type code
    if typecode == 19:  # CT_String
        dataitem.Value.StringValue = write_value
    elif typecode == 6:  # CT_Int16
        dataitem.Value.Int16Value = write_value
    elif typecode == 12:  # CT_Real32
        dataitem.Value.FloatValue = write_value
    elif typecode == 2:  # CT_Boolean
        dataitem.Value.BoolValue = write_value.strip().lower() == "true" # Case sensitive
    else:
        pass

# ---------------------------------------------------------------------------------------
# Attempt to serialize the writing request and catch any errors 
# ---------------------------------------------------------------------------------------

try:
    serialized_writing_request = requestwrite.SerializeToString()
except Exception as e:
    print(" Serialization failed:", e)
    exit(1)

# ---------------------------------------------------------------------------------------
# Call the gRPC methods to write the data. 
# ---------------------------------------------------------------------------------------
writing_method_full_name = f"/{service_name}/{method_name_towrite}"

# Call gRPC WriteSingle method
try:
    response = channel.unary_unary(
        writing_method_full_name,
        request_serializer=lambda _: serialized_writing_request,
        response_deserializer=ResponseClasswrite.FromString
    )(None)

    print("\nResponse message received when writing data (DAE_None = No error):")
    print(response)

    # Optionally, print fields from the response
    for field in response.DESCRIPTOR.fields:
        value = getattr(response, field.name)
        print(f"{field.name}: {value}")

except grpc.RpcError as e:
    print(f"\ngRPC error: {e.code()} - {e.details()}")
     
    
# ---------------------------------------------------------------------------------------
# Create and populate the request for reading
# ---------------------------------------------------------------------------------------
request = RequestClass()
request.portNames.extend(listofvariables)


# ---------------------------------------------------------------------------------------
# Attempt to serialize and catch any errors
# ---------------------------------------------------------------------------------------
try:
    serialized_request = request.SerializeToString()
except Exception as e:
    print(" Serialization failed:", e)
    exit(1)

# ---------------------------------------------------------------------------------------
# Call the gRPC methods to get the data. 
# ---------------------------------------------------------------------------------------

method_full_name = f"/{service_name}/{method_name}"
# Call the gRPC methods
try:
    response = channel.unary_unary(
        method_full_name,
        request_serializer=lambda _: serialized_request,
        response_deserializer=ResponseClass.FromString
    )(request)
 
    listofvariablesread = []

    for i, ret in enumerate(response._ReturnValue):
        value = ret.Value
        var_name = listofvariables[i]

        # Extract the right value type based on TypeCode
        if value.HasField("StringValue"):
            read_val = value.StringValue
        elif value.HasField("Int16Value"):
            read_val = str(value.Int16Value)
        elif value.HasField("FloatValue"):
            read_val = str(value.FloatValue)
        elif value.HasField("BoolValue"):
            read_val = str(value.BoolValue)
        else:
            read_val = "<unsupported type>"

        listofvariablesread.append((var_name, read_val))
    
    print("\nData received after reading request:")
    for var, val in listofvariablesread:
        print(f"{var}: {val}")

except grpc.RpcError as e:
    print(f"\n gRPC error: {e.code()} - {e.details()}")
