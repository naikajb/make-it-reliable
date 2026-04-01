# Tracks the progress of transfers for the server because it needs to be able to track where its at 
#
# this is too complex to track the state of the client because when you run it ur only ever gonna 
# be making one request and be done once u receive what u asked for


# everytime the server is responding to a request with data, a Transfer object needs to be created to track the progress
class Transfer:

    def __init__(self, connection_id, client_addr, filename, file_data, segment_size, transfer_number):
        self.connection_id = connection_id
        self.client_addr = client_addr
        self.filename = filename
        self.file_data = file_data
        self.file_length = len(file_data)
        self.segment_size = segment_size
        self.is_complete = False 
        self.current_chunk = 0  #   goes from 0 to len(file_data)-1
        self.seq_num = 0 #   when we are transfering data, the first sequence number will always be zero. 
        self.transfer_number = transfer_number

        self.chunks = self.split_data(file_data)
        self.total_chunks = len(self.chunks)

        print(f"[SERVER]    Initiatied a Transfer object with {self.total_chunks} chunks of data. Chunk will be {segment_size} bytes")
        
    def split_data(self, data):
        """splits the file content into the appropriate number of chunks"""
        chunks = []
        for i in range(0, max(len(data), 1), self.segment_size):
            chunks.append(data[ i : i + self.segment_size])
        
        return chunks
    
    
    def get_current_chunk(self):
        """ Return the data of the chunk we are currently at"""
        return self.chunks[self.current_chunk]
    
    def next(self):
        """Increments the 'current_chunk' and 'seq_num' vars """
        self.current_chunk += 1
        self.seq_num = 1 - self.seq_num
    


