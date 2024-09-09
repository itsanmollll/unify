import sys

from unify.chat.clients import Client


class ChatBot:  # noqa: WPS338
    """Agent class represents an LLM chat agent."""

    def __init__(
        self,
        client: Client,
    ) -> None:
        """
        Initializes the ChatBot object, wrapped around a client.

        Args:
            client: The Client instance to wrap the chatbot logic around.
        """
        self._paused = False
        assert client.message_content_only, ("ChatBot currently only supports clients which only generate the message "
                                             "content in the return")
        self._client = client

    @property
    def client(self) -> Client:
        """
        Get the client object.  # noqa: DAR201.

        Returns:
            The client.
        """
        return self._client

    def set_client(self, value: client) -> None:
        """
        Set the client.  # noqa: DAR101.

        Args:
            value: The unify client.
        """
        if isinstance(value, Client):
            self._client = value
        else:
            raise Exception("Invalid client!")

    def _get_credits(self) -> float:
        """
        Retrieves the current credit balance from associated with the UNIFY account.

        Returns:
            Current credit balance.
        """
        return self._client.get_credit_balance()

    def _update_message_history(self, role: str, content: str) -> None:
        """
        Updates message history with user input.

        Args:
            role: Either "assistant" or "user".
            content: User input message.
        """
        self._client.messages.append({
            "role": role,
            "content": content,
        })

    def clear_chat_history(self) -> None:
        """Clears the chat history."""
        self._client.set_messages([])

    @staticmethod
    def _stream_response(response) -> str:
        words = ""
        for chunk in response:
            words += chunk
            sys.stdout.write(chunk)
            sys.stdout.flush()
        sys.stdout.write("\n")
        return words

    def run(self, show_credits: bool = False, show_provider: bool = False) -> None:
        """
        Starts the chat interaction loop.

        Args:
            show_credits: Whether to show credit consumption. Defaults to False.
            show_provider: Whether to show the provider used. Defaults to False.
        """
        if not self._paused:
            sys.stdout.write(
                "Let's have a chat. (Enter `pause` to pause and `quit` to exit)\n",
            )
            self.clear_chat_history()
        else:
            sys.stdout.write(
                "Welcome back! (Remember, enter `pause` to pause and `quit` to exit)\n",
            )
        self._paused = False
        while True:
            sys.stdout.write("> ")
            inp = input()
            if inp == "quit":
                self.clear_chat_history()
                break
            elif inp == "pause":
                self._paused = True
                break
            self._update_message_history(role="user", content=inp)
            initial_credit_balance = self._get_credits()
            response = self._client.generate()
            if self._client.stream:
                words = self._stream_response(response)
            else:
                words = response
                sys.stdout.write(words)
                sys.stdout.write("\n")
            self._update_message_history(
                role="assistant",
                content=words,
            )
            final_credit_balance = self._get_credits()
            if show_credits:
                sys.stdout.write(
                    "\n(spent {:.6f} credits)".format(
                        initial_credit_balance - final_credit_balance,
                    ),
                )
            if show_provider:
                sys.stdout.write("\n(provider: {})".format(self._client.provider))