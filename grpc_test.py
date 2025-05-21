import grpc
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('./pxc_grpc'))

# Print the Python path to verify
# print(sys.path)

from pxc_grpc.Plc.Gds.IDataAccessService_pb2 import IDataAccessServiceReadSingleRequest, \
    IDataAccessServiceReadRequest, IDataAccessServiceWriteSingleRequest, IDataAccessServiceWriteRequest
from pxc_grpc.Plc.Gds.IDataAccessService_pb2_grpc import IDataAccessServiceStub
from pxc_grpc.Plc.Gds.WriteItem_pb2 import WriteItem


def write_single_string(stub, port_name, value):
    
    single_write_request = IDataAccessServiceWriteSingleRequest()
    single_write_request.data.PortName = port_name
    single_write_request.data.Value.TypeCode = 19
    single_write_request.data.Value.StringValue = value

    return stub.WriteSingle(single_write_request)


def write_single_int(stub, port_name, value):
    
    single_write_request = IDataAccessServiceWriteSingleRequest()
    single_write_request.data.PortName = port_name
    single_write_request.data.Value.TypeCode = 6
    single_write_request.data.Value.Int16Value = value

    return stub.WriteSingle(single_write_request)


def write_multiple_values(stub):

    write_request = IDataAccessServiceWriteRequest()

    wi1 = WriteItem()
    wi1.PortName = 'Arp.Plc.Eclr/MainInstance.strInput'
    wi1.Value.StringValue = "This text has just been copied"
    wi1.Value.TypeCode = 19
    
    wi2 = WriteItem()
    wi2.PortName = 'Arp.Plc.Eclr/MainInstance.strInput2'
    wi2.Value.StringValue = "The gRPC communication seems to work"
    wi2.Value.TypeCode = 19
    
    wi3 = WriteItem()
    wi3.PortName = 'Arp.Plc.Eclr/MainInstance.xInput'
    wi3.Value.StringValue = "True"
    wi3.Value.TypeCode = 2

    # add multiple WriteItems at once
    write_request.data.extend([wi1, wi2, wi3])

    # add WriteItems separately
    # response1.data.append(wi1)
    # response1.data.append(wi2)

    return stub.Write(write_request)


def read_single_value(stub, port_name):

    single_read_request = IDataAccessServiceReadSingleRequest()
    single_read_request.portName=port_name

    return stub.ReadSingle(single_read_request)


def read_multiple_values(stub, port_names):

    read_request = IDataAccessServiceReadRequest()
    read_request.portNames.extend(port_names)

    return stub.Read(read_request)


if __name__ == "__main__":
   
    # create channel and stub
    channel = grpc.insecure_channel('unix:/run/plcnext/grpc.sock')
    stub = IDataAccessServiceStub(channel)

    print(write_single_string(stub, 'Arp.Plc.Eclr/MainInstance.strInput', 'test123'))
    print(write_single_int(stub, 'Arp.Plc.Eclr/MainInstance.iInput', 18))

    print(write_multiple_values(stub))

    r = read_single_value(stub, 'Arp.Plc.Eclr/MainInstance.strInput')
    print(r)
    print(r._ReturnValue.Value.TypeCode)
    print(r._ReturnValue.Value.StringValue)

    r = read_multiple_values(stub, ['Arp.Plc.Eclr/MainInstance.iInput', 'Arp.Plc.Eclr/MainInstance.strInput'])
    for value in r._ReturnValue:
        print(value, value.Value.TypeCode)
