class DarwinController:
    def __init__(self):
        self.idle_flag = True
        self.response_flag = False

    def set_idle(self):
        self.idle_flag = True
        self.response_flag = False
        print(f"[INFO] set_idle called: idle_flag = {self.idle_flag}, response_flag = {self.response_flag}")

    def set_response(self):
        self.idle_flag = False
        self.response_flag = True
        print(f"[INFO] set_response called: idle_flag = {self.idle_flag}, response_flag = {self.response_flag}")

    def is_idle(self):
        return self.idle_flag

    def is_response(self):
        return self.response_flag

    def get_state(self):
        if self.idle_flag:
            return 'idle'
        elif self.response_flag:
            return 'response'
        else:
            return 'unknown'  # If there’s any unexpected state
