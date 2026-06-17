from memory.profile_store import (
    get_profile,
    update_profile,
    create_patient,
    login_with_email,
    email_exists
)

from memory.chat_store import (
    get_chat_history,
    save_message
)

from memory.qa_store import (
    save_qa,
    get_patient_qa
)

from memory.session_store import (
    create_session,
    add_message
)

class MemoryManager:

    def __init__(self, user_id):

        self.user_id = user_id

    def save_user_message(
        self,
        message
    ):

        save_message(
            self.user_id,
            "user",
            message
        )

    @staticmethod
    def create_new_patient(
    name,
    age,
    gender,
    email,
    password):
        
        return create_patient(
        name,
        age,
        gender,
        email,
        password
    )
    
    
    def save_assistant_message(
        self,
        message
    ):

        save_message(
            self.user_id,
            "assistant",
            message
        )
    @staticmethod
    def login_by_email(
        email,
        password
    ):

        return login_with_email(
            email,
            password
        )


    @staticmethod
    def email_already_exists(
        email
    ):

        return email_exists(email)

    def get_history(self):

        return get_chat_history(
            self.user_id
        )

    def get_profile(self):

        return get_profile(
            self.user_id
        )

    def add_concern(
        self,
        concern
    ):

        update_profile(
            self.user_id,
            concern=concern
        )

    def add_note(
        self,
        note
    ):

        update_profile(
            self.user_id,
            note=note
        )
    def save_qa_record(
    self,
    question,
    answer
):
        

        save_qa(
        self.user_id,
        question,
        answer
    )


    def get_qa_history(self):

        return get_patient_qa(
            self.user_id
        )


    def start_session(self):

        return create_session(
            self.user_id
        )


    def add_session_message(
        self,
        session_index,
        role,
        content
    ):

        add_message(
            self.user_id,
            session_index,
            role,
            content
        )
    def list_users(self):
        from memory.profile_store import _load_profiles
        profiles = _load_profiles()
        return list(profiles.keys())
    