import ecal.nanobind_core as ecal_core


class EcalPublisher:
    def __init__(self, topic_name, descriptor_file, type_name):
        ecal_core.initialize("Video Publisher")

        with open(descriptor_file, 'rb') as f:
            descriptor_bytes = f.read()

        self.data_type_info = ecal_core.DataTypeInformation(
            name=type_name,
            encoding="proto",
            descriptor=descriptor_bytes
        )

        self.pub = ecal_core.Publisher(topic_name, self.data_type_info)

    def send(self, msg):
        """Envia un mensaje protobuf serializado."""
        serialized = msg.SerializeToString()
        self.pub.send(serialized)
        return len(serialized)

    def close(self):
        ecal_core.finalize()


class EcalSubscriber:
    def __init__(self, topic_name, descriptor_file, type_name, callback):
        ecal_core.initialize("Video Subscriber")

        with open(descriptor_file, 'rb') as f:
            descriptor_bytes = f.read()

        self.data_type_info = ecal_core.DataTypeInformation(
            name=type_name,
            encoding="proto",
            descriptor=descriptor_bytes
        )

        self.sub = ecal_core.Subscriber(topic_name, self.data_type_info)
        self.sub.set_receive_callback(callback)

    def close(self):
        self.sub.remove_receive_callback()
        ecal_core.finalize()
