# global
import openai
from openai._types import Headers as OpenAIHeaders,\
    Query as OpenAIQuery,\
    Body as OpenAIBody
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionMessageParam,
    ChatCompletionStreamOptionsParam,
)
from openai.types.chat.completion_create_params import ResponseFormat
import requests
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Mapping, Dict, Generator, List, Optional, Union, \
    Iterable

# local
import unify
from unify import BASE_URL
from unify.queries import Query
from unify._caching import _get_cache, _write_to_cache
from unify.utils.helpers import _validate_api_key, _default
from unify.exceptions import BadRequestError, UnifyError, status_error_map


class Client(ABC):
    """Base Abstract class for interacting with the Unify chat completions endpoint."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        *,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[Iterable[ChatCompletionMessageParam]] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = 1024,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        stream: Optional[bool] = False,
        stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        # python client arguments
        message_content_only: bool = True,
        cache: bool = False,
        # passthrough arguments
        extra_headers: Optional[OpenAIHeaders] = None,
        extra_query: Optional[OpenAIQuery] = None,
        **kwargs,
    ) -> None:  # noqa: DAR101, DAR401
        """Initialize the Unify client.

        Args:
            endpoint: Endpoint name in OpenAI API format:
            <model_name>@<provider_name>
            Defaults to None.

            model: Name of the model. Should only be set if endpoint is not set.

            provider: Name of the provider. Should only be set if endpoint is not set.

            system_prompt: An optional string containing the system prompt.

            messages: A list of messages comprising the conversation so far.
            If provided, user_prompt must be None.

            api_key: API key for accessing the Unify API.
            If None, it attempts to retrieve the API key from the environment variable
            UNIFY_KEY. Defaults to None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self._api_key = _validate_api_key(api_key)
        if endpoint and (model or provider):
            raise UnifyError(
                "if the model or provider are passed, then the endpoint must not be"
                "passed."
            )
        self._endpoint = None
        if endpoint:
            self.set_endpoint(endpoint)
        self._provider = None
        if provider:
            self.set_provider(provider)
        self._model = None
        if model:
            self.set_model(model)
        self._system_prompt = None
        self.set_system_prompt(system_prompt)
        self._messages = None
        self.set_messages(messages)
        self._frequency_penalty = None
        self.set_frequency_penalty(frequency_penalty)
        self._logit_bias = None
        self.set_logit_bias(logit_bias)
        self._logprobs = None
        self.set_logprobs(logprobs)
        self._top_logprobs = None
        self.set_top_logprobs(top_logprobs)
        self._max_tokens = None
        self.set_max_tokens(max_tokens)
        self._n = None
        self.set_n(n)
        self._presence_penalty = None
        self.set_presence_penalty(presence_penalty)
        self._response_format = None
        self.set_response_format(response_format)
        self._seed = None
        self.set_seed(seed)
        self._stop = None
        self.set_stop(stop)
        self._stream = None
        self.set_stream(stream)
        self._stream_options = None
        self.set_stream_options(stream_options)
        self._temperature = None
        self.set_temperature(temperature)
        self._top_p = None
        self.set_top_p(top_p)
        self._tools = None
        self.set_tools(tools)
        self._tool_choice = None
        self.set_tool_choice(tool_choice)
        self._parallel_tool_calls = None
        self.set_parallel_tool_calls(parallel_tool_calls)
        # platform arguments
        self._use_custom_keys = None
        self.set_use_custom_keys(use_custom_keys)
        self._tags = None
        self.set_tags(tags)
        # python client arguments
        self._message_content_only = None
        self.set_message_content_only(message_content_only)
        self._cache = None
        self.set_cache(cache)
        # passthrough arguments
        self._extra_headers = None
        self.set_extra_headers(extra_headers)
        self._extra_query = None
        self.set_extra_query(extra_query)
        self._extra_body = None
        self.set_extra_body(kwargs)
        self._client = self._get_client()

    # Properties #
    # -----------#

    @property
    def endpoint(self) -> str:
        """
        Get the endpoint name.

        Returns:
            The endpoint name.
        """
        return self._endpoint

    @property
    def model(self) -> str:
        """
        Get the model name.

        Returns:
            The model name.
        """
        return self._model

    @property
    def provider(self) -> str:
        """
        Get the provider name.

        Returns:
            The provider name.
        """
        return self._provider

    @property
    def system_prompt(self) -> Optional[str]:
        """
        Get the default system prompt, if set.

        Returns:
            The default system prompt.
        """
        return self._system_prompt

    @property
    def messages(self) -> Optional[Iterable[ChatCompletionMessageParam]]:
        """
        Get the default messages, if set.

        Returns:
            The default messages.
        """
        return self._messages

    @property
    def frequency_penalty(self) -> Optional[float]:
        """
        Get the default frequency penalty, if set.

        Returns:
            The default frequency penalty.
        """
        return self._frequency_penalty

    @property
    def logit_bias(self) -> Optional[Dict[str, int]]:
        """
        Get the default logit bias, if set.

        Returns:
            The default logit bias.
        """
        return self._logit_bias

    @property
    def logprobs(self) -> Optional[bool]:
        """
        Get the default logprobs, if set.

        Returns:
            The default logprobs.
        """
        return self._logprobs

    @property
    def top_logprobs(self) -> Optional[int]:
        """
        Get the default top logprobs, if set.

        Returns:
            The default top logprobs.
        """
        return self._top_logprobs

    @property
    def max_tokens(self) -> Optional[int]:
        """
        Get the default max tokens, if set.

        Returns:
            The default max tokens.
        """
        return self._max_tokens

    @property
    def n(self) -> Optional[int]:
        """
        Get the default n, if set.

        Returns:
            The default n value.
        """
        return self._n

    @property
    def presence_penalty(self) -> Optional[float]:
        """
        Get the default presence penalty, if set.

        Returns:
            The default presence penalty.
        """
        return self._presence_penalty

    @property
    def response_format(self) -> Optional[ResponseFormat]:
        """
        Get the default response format, if set.

        Returns:
            The default response format.
        """
        return self._response_format

    @property
    def seed(self) -> Optional[int]:
        """
        Get the default seed value, if set.

        Returns:
            The default seed value.
        """
        return self._seed

    @property
    def stop(self) -> Union[Optional[str], List[str]]:
        """
        Get the default stop value, if set.

        Returns:
            The default stop value.
        """
        return self._stop

    @property
    def stream(self) -> Optional[bool]:
        """
         Get the default stream bool, if set.

         Returns:
             The default stream bool.
         """
        return self._stream

    @property
    def stream_options(self) -> Optional[ChatCompletionStreamOptionsParam]:
        """
         Get the default stream options, if set.

         Returns:
             The default stream options.
         """
        return self._stream_options

    @property
    def temperature(self) -> Optional[float]:
        """
         Get the default temperature, if set.

         Returns:
             The default temperature.
         """
        return self._temperature

    @property
    def top_p(self) -> Optional[float]:
        """
         Get the default top p value, if set.

         Returns:
             The default top p value.
         """
        return self._top_p

    @property
    def tools(self) -> Optional[Iterable[ChatCompletionToolParam]]:
        """
         Get the default tools, if set.

         Returns:
             The default tools.
         """
        return self._tools

    @property
    def tool_choice(self) -> Optional[ChatCompletionToolChoiceOptionParam]:
        """
         Get the default tool choice, if set.

         Returns:
             The default tool choice.
         """
        return self._tool_choice

    @property
    def parallel_tool_calls(self) -> Optional[bool]:
        """
         Get the default parallel tool calls bool, if set.

         Returns:
             The default parallel tool calls bool.
         """
        return self._parallel_tool_calls

    @property
    def use_custom_keys(self) -> bool:
        """
         Get the default use custom keys bool, if set.

         Returns:
             The default use custom keys bool.
         """
        return self._use_custom_keys

    @property
    def tags(self) -> Optional[List[str]]:
        """
         Get the default tags, if set.

         Returns:
             The default tags.
         """
        return self._tags

    @property
    def message_content_only(self) -> bool:
        """
          Get the default message content only bool.

          Returns:
              The default message content only bool.
          """
        return self._message_content_only

    @property
    def cache(self) -> bool:
        """
          Get default the cache bool.

          Returns:
              The default cache bool.
          """
        return self._cache

    @property
    def extra_headers(self) -> Optional[OpenAIHeaders]:
        """
         Get the default extra headers, if set.

         Returns:
             The default extra headers.
         """
        return self._extra_headers

    @property
    def extra_query(self) -> Optional[OpenAIQuery]:
        """
         Get the default extra query, if set.

         Returns:
             The default extra query.
         """
        return self._extra_query

    @property
    def extra_body(self) -> Optional[Mapping[str, str]]:
        """
         Get the default extra body, if set.

         Returns:
             The default extra body.
         """
        return self._extra_body

    # Setters #
    # --------#

    def set_endpoint(self, value: str) -> None:
        """
        Set the endpoint name.  # noqa: DAR101.

        Args:
            value: The endpoint name.
        """
        valid_endpoints = unify.list_endpoints(api_key=self._api_key)
        if value not in valid_endpoints:
            raise UnifyError(
                "The specified endpoint {} is not one of the endpoints supported by "
                "Unify: {}".format(value, valid_endpoints)
            )
        self._endpoint = value
        self._model, self._provider = value.split("@")  # noqa: WPS414

    def set_model(self, value: str) -> None:
        """
        Set the model name.  # noqa: DAR101.

        Args:
            value: The model name.
        """
        valid_models = unify.list_models(self._provider, api_key=self._api_key)
        if value not in valid_models:
            if self._provider:
                raise UnifyError(
                    "Current provider {} does not support the specified model {},"
                    "please select one of: {}".format(
                        self._provider, value, valid_models
                    )
                )
            raise UnifyError(
                "The specified model {} is not one of the models supported by Unify: {}".format(
                    value, valid_models
                )
            )
        self._model = value
        if self._provider:
            self._endpoint = "@".join([value, self._provider])

    def set_provider(self, value: str) -> None:
        """
        Set the provider name.  # noqa: DAR101.

        Args:
            value: The provider name.
        """
        valid_providers = unify.list_providers(self._model, api_key=self._api_key)
        if value not in valid_providers:
            if self._model:
                raise UnifyError(
                    "Current model {} does not support the specified provider {},"
                    "please select one of: {}".format(
                        self._model, value, valid_providers
                    )
                )
            raise UnifyError(
                "The specified provider {} is not one of the providers supported by "
                "Unify: {}".format(value, valid_providers)
            )
        self._provider = value
        if self._model:
            self._endpoint = "@".join([self._model, value])

    def set_system_prompt(self, value: str) -> None:
        """
        Set the default system prompt.  # noqa: DAR101.

        Args:
            value: The default system prompt.
        """
        self._system_prompt = value

    def set_messages(self, value: Iterable[ChatCompletionMessageParam]) -> None:
        """
        Set the default messages.  # noqa: DAR101.

        Args:
            value: The default messages.
        """
        self._messages = value

    def set_frequency_penalty(self, value: float) -> None:
        """
        Set the default frequency penalty.  # noqa: DAR101.

        Args:
            value: The default frequency penalty.
        """
        self._frequency_penalty = value

    def set_logit_bias(self, value: Dict[str, int]) -> None:
        """
        Set the default logit bias.  # noqa: DAR101.

        Args:
            value: The default logit bias.
        """
        self._logit_bias = value

    def set_logprobs(self, value: bool) -> None:
        """
        Set the default logprobs.  # noqa: DAR101.

        Args:
            value: The default logprobs.
        """
        self._logprobs = value

    def set_top_logprobs(self, value: int) -> None:
        """
        Set the default top logprobs.  # noqa: DAR101.

        Args:
            value: The default top logprobs.
        """
        self._top_logprobs = value

    def set_max_tokens(self, value: int) -> None:
        """
        Set the default max tokens.  # noqa: DAR101.

        Args:
            value: The default max tokens.
        """
        self._max_tokens = value

    def set_n(self, value: int) -> None:
        """
        Set the default n value.  # noqa: DAR101.

        Args:
            value: The default n value.
        """
        self._n = value

    def set_presence_penalty(self, value: float) -> None:
        """
        Set the default presence penalty.  # noqa: DAR101.

        Args:
            value: The default presence penalty.
        """
        self._presence_penalty = value

    def set_response_format(self, value: ResponseFormat) -> None:
        """
        Set the default response format.  # noqa: DAR101.

        Args:
            value: The default response format.
        """
        self._response_format = value

    def set_seed(self, value: int) -> None:
        """
        Set the default seed value.  # noqa: DAR101.

        Args:
            value: The default seed value.
        """
        self._seed = value

    def set_stop(self, value: Union[str, List[str]]) -> None:
        """
        Set the default stop value.  # noqa: DAR101.

        Args:
            value: The default stop value.
        """
        self._stop = value

    def set_stream(self, value: bool) -> None:
        """
        Set the default stream bool.  # noqa: DAR101.

        Args:
            value: The default stream bool.
        """
        self._stream = value

    def set_stream_options(self, value: ChatCompletionStreamOptionsParam) -> None:
        """
        Set the default stream options.  # noqa: DAR101.

        Args:
            value: The default stream options.
        """
        self._stream_options = value

    def set_temperature(self, value: float) -> None:
        """
        Set the default temperature.  # noqa: DAR101.

        Args:
            value: The default temperature.
        """
        self._temperature = value

    def set_top_p(self, value: float) -> None:
        """
        Set the default top p value.  # noqa: DAR101.

        Args:
            value: The default top p value.
        """
        self._top_p = value

    def set_tools(self, value: Iterable[ChatCompletionToolParam]) -> None:
        """
        Set the default tools.  # noqa: DAR101.

        Args:
            value: The default tools.
        """
        self._tools = value

    def set_tool_choice(self, value: ChatCompletionToolChoiceOptionParam) -> None:
        """
        Set the default tool choice.  # noqa: DAR101.

        Args:
            value: The default tool choice.
        """
        self._tool_choice = value

    def set_parallel_tool_calls(self, value: bool) -> None:
        """
        Set the default parallel tool calls bool.  # noqa: DAR101.

        Args:
            value: The default parallel tool calls bool.
        """
        self._parallel_tool_calls = value

    def set_use_custom_keys(self, value: bool) -> None:
        """
        Set the default use custom keys bool.  # noqa: DAR101.

        Args:
            value: The default use custom keys bool.
        """
        self._use_custom_keys = value

    def set_tags(self, value: List[str]) -> None:
        """
        Set the default tags.  # noqa: DAR101.

        Args:
            value: The default tags.
        """
        self._tags = value

    def set_message_content_only(self, value: bool) -> None:
        """
        Set the default message content only bool.  # noqa: DAR101.

        Args:
            value: The default message content only bool.
        """
        self._message_content_only = value

    def set_cache(self, value: bool) -> None:
        """
        Set the default cache bool.  # noqa: DAR101.

        Args:
            value: The default cache bool.
        """
        self._cache = value

    def set_extra_headers(self, value: OpenAIHeaders) -> None:
        """
        Set the default extra headers.  # noqa: DAR101.

        Args:
            value: The default extra headers.
        """
        self._extra_headers = value

    def set_extra_query(self, value: OpenAIQuery) -> None:
        """
        Set the default extra query.  # noqa: DAR101.

        Args:
            value: The default extra query.
        """
        self._extra_query = value

    def set_extra_body(self, value: OpenAIBody) -> None:
        """
        Set the default extra body.  # noqa: DAR101.

        Args:
            value: The default extra body.
        """
        self._extra_body = value

    # Generate #
    # ---------#

    def generate(
        self,
        user_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[Iterable[ChatCompletionMessageParam]] = None,
        *,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = 1024,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        stream: Optional[bool] = False,
        stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        # python client arguments
        message_content_only: bool = True,
        cache: bool = False,
        # passthrough arguments
        extra_headers: Optional[OpenAIHeaders] = None,
        extra_query: Optional[OpenAIQuery] = None,
        **kwargs,
    ):
        """Generate content using the Unify API.

        Args:
            user_prompt: A string containing the user prompt.
            If provided, messages must be None.

            system_prompt: An optional string containing the system prompt.

            messages: A list of messages comprising the conversation so far.
            If provided, user_prompt must be None.

            frequency_penalty: Number between -2.0 and 2.0. Positive values penalize new
            tokens based on their existing frequency in the text so far, decreasing the
            model's likelihood to repeat the same line verbatim.

            logit_bias: Modify the likelihood of specified tokens appearing in the
            completion. Accepts a JSON object that maps tokens (specified by their token
            ID in the tokenizer) to an associated bias value from -100 to 100.
            Mathematically, the bias is added to the logits generated by the model prior
            to sampling. The exact effect will vary per model, but values between -1 and
            1 should decrease or increase likelihood of selection; values like -100 or
            100 should result in a ban or exclusive selection of the relevant token.

            logprobs: Whether to return log probabilities of the output tokens or not.
            If true, returns the log probabilities of each output token returned in the
            content of message.

            top_logprobs: An integer between 0 and 20 specifying the number of most
            likely tokens to return at each token position, each with an associated log
            probability. logprobs must be set to true if this parameter is used.

            max_tokens: The maximum number of tokens that can be generated in the chat
            completion. The total length of input tokens and generated tokens is limited
            by the model's context length. Defaults to the provider's default max_tokens
            when the value is None.

            n: How many chat completion choices to generate for each input message. Note
            that you will be charged based on the number of generated tokens across all
            of the choices. Keep n as 1 to minimize costs.

            presence_penalty: Number between -2.0 and 2.0. Positive values penalize new
            tokens based on whether they appear in the text so far, increasing the
            model's likelihood to talk about new topics.

            response_format: An object specifying the format that the model must output.
            Setting to `{ "type": "json_schema", "json_schema": {...} }` enables
            Structured Outputs which ensures the model will match your supplied JSON
            schema. Learn more in the Structured Outputs guide. Setting to
            `{ "type": "json_object" }` enables JSON mode, which ensures the message the
            model generates is valid JSON.

            seed: If specified, a best effort attempt is made to sample
            deterministically, such that repeated requests with the same seed and
            parameters should return the same result. Determinism is not guaranteed, and
            you should refer to the system_fingerprint response parameter to monitor
            changes in the backend.

            stop: Up to 4 sequences where the API will stop generating further tokens.

            stream: If True, generates content as a stream. If False, generates content
            as a single response. Defaults to False.

            stream_options: Options for streaming response. Only set this when you set
            stream: true.

            temperature:  What sampling temperature to use, between 0 and 2.
            Higher values like 0.8 will make the output more random,
            while lower values like 0.2 will make it more focused and deterministic.
            It is generally recommended to alter this or top_p, but not both.
            Defaults to the provider's default max_tokens when the value is None.

            top_p: An alternative to sampling with temperature, called nucleus sampling,
            where the model considers the results of the tokens with top_p probability
            mass. So 0.1 means only the tokens comprising the top 10% probability mass
            are considered. Generally recommended to alter this or temperature, but not
            both.

            tools: A list of tools the model may call. Currently, only functions are
            supported as a tool. Use this to provide a list of functions the model may
            generate JSON inputs for. A max of 128 functions are supported.

            tool_choice: Controls which (if any) tool is called by the
            model. none means the model will not call any tool and instead generates a
            message. auto means the model can pick between generating a message or
            calling one or more tools. required means the model must call one or more
            tools. Specifying a particular tool via
            `{ "type": "function", "function": {"name": "my_function"} }`
            forces the model to call that tool.
            none is the default when no tools are present. auto is the default if tools
            are present.

            parallel_tool_calls: Whether to enable parallel function calling during tool
            use.

            use_custom_keys:  Whether to use custom API keys or our unified API keys
            with the backend provider.

            tags: Arbitrary number of tags to classify this API query as needed. Helpful
            for generally grouping queries across tasks and users, for logging purposes.

            message_content_only: If True, only return the message content
            chat_completion.choices[0].message.content.strip(" ") from the OpenAI
            return. Otherwise, the full response chat_completion is returned.
            Defaults to True.

            cache: If True, then the arguments will be stored in a local cache file, and
            any future calls with identical arguments will read from the cache instead
            of running the LLM query. This can help to save costs and also debug
            multi-step LLM applications, while keeping early steps fixed.
            This argument only has any effect when stream=False.

            extra_headers: Additional "passthrough" headers for the request which are
            provider-specific, and are not part of the OpenAI standard. They are handled
            by the provider-specific API.

            extra_query: Additional "passthrough" query parameters for the request which
            are provider-specific, and are not part of the OpenAI standard. They are
            handled by the provider-specific API.

            kwargs: Additional "passthrough" JSON properties for the body of the
            request, which are provider-specific, and are not part of the OpenAI
            standard. They will be handled by the provider-specific API.

        Returns:
            If stream is True, returns a generator yielding chunks of content.
            If stream is False, returns a single string response.

        Raises:
            UnifyError: If an error occurs during content generation.
        """
        return self._generate(
            user_prompt,
            _default(system_prompt, self._system_prompt),
            _default(messages, self._messages),
            frequency_penalty=_default(frequency_penalty, self._frequency_penalty),
            logit_bias=_default(logit_bias, self._logit_bias),
            logprobs=_default(logprobs, self._logprobs),
            top_logprobs=_default(top_logprobs, self._top_logprobs),
            max_tokens=_default(max_tokens, self._max_tokens),
            n=_default(n, self._n),
            presence_penalty=_default(presence_penalty, self._presence_penalty),
            response_format=_default(response_format, self._response_format),
            seed=_default(seed, self._seed),
            stop=_default(stop, self._stop),
            stream=_default(stream, self._stream),
            stream_options=_default(stream_options, self._stream_options),
            temperature=_default(temperature, self._temperature),
            top_p=_default(top_p, self._top_p),
            tools=_default(tools, self._tools),
            tool_choice=_default(tool_choice, self._tool_choice),
            parallel_tool_calls=_default(parallel_tool_calls,
                                         self._parallel_tool_calls),
            # platform arguments
            use_custom_keys=_default(use_custom_keys, self._use_custom_keys),
            tags=_default(tags, self._tags),
            # python client arguments
            message_content_only=_default(message_content_only,
                                          self._message_content_only),
            cache=_default(cache, self._cache),
            # passthrough arguments
            extra_headers=_default(extra_headers, self._extra_headers),
            extra_query=_default(extra_query, self._extra_query),
            **{**self._extra_body, **kwargs},
        )

    # Credits #
    # --------#

    def get_credit_balance(self) -> Union[float, None]:
        # noqa: DAR201, DAR401
        """
        Get the remaining credits left on your account.

        Returns:
            The remaining credits on the account if successful, otherwise None.
        Raises:
            BadRequestError: If there was an HTTP error.
            ValueError: If there was an error parsing the JSON response.
        """
        url = f"{BASE_URL}/credits"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()["credits"]
        except requests.RequestException as e:
            raise BadRequestError("There was an error with the request.") from e
        except (KeyError, ValueError) as e:
            raise ValueError("Error parsing JSON response.") from e

    # Abstract Methods #
    # -----------------#

    @abstractmethod
    def _get_client(self):
        raise NotImplementedError

    @abstractmethod
    def _generate(
            self,
            user_prompt: Optional[str] = None,
            system_prompt: Optional[str] = None,
            messages: Optional[Iterable[ChatCompletionMessageParam]] = None,
            *,
            frequency_penalty: Optional[float] = None,
            logit_bias: Optional[Dict[str, int]] = None,
            logprobs: Optional[bool] = None,
            top_logprobs: Optional[int] = None,
            max_tokens: Optional[int] = 1024,
            n: Optional[int] = None,
            presence_penalty: Optional[float] = None,
            response_format: Optional[ResponseFormat] = None,
            seed: Optional[int] = None,
            stop: Union[Optional[str], List[str]] = None,
            stream: Optional[bool] = False,
            stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
            temperature: Optional[float] = 1.0,
            top_p: Optional[float] = None,
            tools: Optional[Iterable[ChatCompletionToolParam]] = None,
            tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
            parallel_tool_calls: Optional[bool] = None,
            # platform arguments
            use_custom_keys: bool = False,
            tags: Optional[List[str]] = None,
            # python client arguments
            message_content_only: bool = True,
            cache: bool = False,
            # passthrough arguments
            extra_headers: Optional[OpenAIHeaders] = None,
            extra_query: Optional[OpenAIQuery] = None,
            **kwargs,
    ):
        raise NotImplementedError


class Unify(Client):
    """Class for interacting with the Unify chat completions endpoint in a synchronous
    manner."""

    def _get_client(self):
        try:
            return openai.OpenAI(
                base_url=f"{BASE_URL}",
                api_key=self._api_key,
            )
        except openai.OpenAIError as e:
            raise UnifyError(f"Failed to initialize Unify client: {str(e)}")

    def _generate_stream(
        self,
        endpoint: str,
        query: Query,
        # stream
        stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        # python client arguments
        message_content_only: bool = True,
    ) -> Generator[str, None, None]:
        query_dict = query.model_dump()
        if "extra_body" in query_dict:
            extra_body = query_dict["extra_body"]
            del query_dict["extra_body"]
        else:
            extra_body = {}
        kw = dict(
            model=endpoint,
            **query_dict,
            stream=True,
            stream_options=stream_options,
            extra_body={  # platform arguments
                "signature": "python",
                "use_custom_keys": use_custom_keys,
                "tags": tags,
                # passthrough json arguments
                **extra_body,
            }
        )
        kw = {k: v for k, v in kw.items() if v is not None}
        try:
            chat_completion = self._client.chat.completions.create(**kw)
            for chunk in chat_completion:
                if message_content_only:
                    content = chunk.choices[0].delta.content  # type: ignore[union-attr]    # noqa: E501
                else:
                    content = chunk
                self.set_provider(chunk.model.split("@")[-1])  # type: ignore[union-attr]   # noqa: E501
                if content is not None:
                    yield content
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None

    def _generate_non_stream(
        self,
        endpoint: str,
        query: Query,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        # python client arguments
        message_content_only: bool = True,
        cache: bool = False,
    ) -> str:
        query_dict = query.model_dump()
        if "extra_body" in query_dict:
            extra_body = query_dict["extra_body"]
            del query_dict["extra_body"]
        else:
            extra_body = {}
        kw = dict(
            model=endpoint,
            **query_dict,
            extra_body={  # platform arguments
                "signature": "python",
                "use_custom_keys": use_custom_keys,
                "tags": tags,
                # passthrough json arguments
                **extra_body,
            }
        )
        kw = {k: v for k, v in kw.items() if v is not None}
        chat_completion = None
        if cache:
            chat_completion = _get_cache(kw)
        if chat_completion is None:
            try:
                chat_completion = self._client.chat.completions.create(**kw)
            except openai.APIStatusError as e:
                raise status_error_map[e.status_code](e.message) from None
            if cache:
                _write_to_cache(kw, chat_completion)
        if "router" not in endpoint:
            self.set_provider(
                chat_completion.model.split(  # type: ignore[union-attr]
                    "@",
                )[-1]
            )
        if message_content_only:
            content = chat_completion.choices[0].message.content
            if content:
                return content.strip(" ")
            return ""
        return chat_completion

    def _generate(  # noqa: WPS234, WPS211
        self,
        user_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[Iterable[ChatCompletionMessageParam]] = None,
        *,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = 1024,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        stream: Optional[bool] = False,
        stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        # python client arguments
        message_content_only: bool = True,
        cache: bool = False,
        # passthrough arguments
        extra_headers: Optional[OpenAIHeaders] = None,
        extra_query: Optional[OpenAIQuery] = None,
        **kwargs,
    ) -> Union[Generator[str, None, None], str]:  # noqa: DAR101, DAR201, DAR401
        contents = []
        if system_prompt:
            contents.append({"role": "system", "content": system_prompt})
        if user_prompt:
            contents.append({"role": "user", "content": user_prompt})
        elif messages:
            contents.extend(messages)
        else:
            raise UnifyError("You must provider either the user_prompt or messages!")

        if tools:
            message_content_only = False

        query = Query(
            messages=contents,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            max_tokens=max_tokens,
            n=n,
            presence_penalty=presence_penalty,
            response_format=response_format,
            seed=seed,
            stop=stop,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=kwargs
        )
        if stream:
            return self._generate_stream(
                self._endpoint,
                query,
                # stream
                stream_options=stream_options,
                # platform arguments
                use_custom_keys=use_custom_keys,
                tags=tags,
                # python client arguments
                message_content_only=message_content_only
            )
        return self._generate_non_stream(
            self._endpoint,
            query,
            # platform arguments
            use_custom_keys=use_custom_keys,
            tags=tags,
            # python client arguments
            message_content_only=message_content_only,
            cache=cache
        )


class AsyncUnify(Client):
    """Class for interacting with the Unify chat completions endpoint in a synchronous
    manner."""

    def _get_client(self):
        try:
            return openai.AsyncOpenAI(
                base_url=f"{BASE_URL}",
                api_key=self._api_key,
            )
        except openai.APIStatusError as e:
            raise UnifyError(f"Failed to initialize Unify client: {str(e)}")

    async def _generate_stream(
        self,
        endpoint: str,
        query: Query,
        # stream
        stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        # python client arguments
        message_content_only: bool = True,
    ) -> AsyncGenerator[str, None]:
        query_dict = query.model_dump()
        if "extra_body" in query_dict:
            extra_body = query_dict["extra_body"]
            del query_dict["extra_body"]
        else:
            extra_body = {}
        kw = dict(
            model=endpoint,
            **query_dict,
            stream=True,
            stream_options=stream_options,
            extra_body={  # platform arguments
                "signature": "python",
                "use_custom_keys": use_custom_keys,
                "tags": tags,
                # passthrough json arguments
                **extra_body,
            }
        )
        kw = {k: v for k, v in kw.items() if v is not None}
        try:
            async_stream = await self._client.chat.completions.create(**kw)
            async for chunk in async_stream:  # type: ignore[union-attr]
                self.set_provider(chunk.model.split("@")[-1])
                if message_content_only:
                    yield chunk.choices[0].delta.content or ""
                yield chunk
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None

    async def _generate_non_stream(
        self,
        endpoint: str,
        query: Query,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        # python client arguments
        message_content_only: bool = True,
        cache: bool = False
    ) -> str:
        query_dict = query.model_dump()
        if "extra_body" in query_dict:
            extra_body = query_dict["extra_body"]
            del query_dict["extra_body"]
        else:
            extra_body = {}
        kw = dict(
            model=endpoint,
            **query_dict,
            extra_body={  # platform arguments
                "signature": "python",
                "use_custom_keys": use_custom_keys,
                "tags": tags,
                # passthrough json arguments
                **extra_body,
            }
        )
        kw = {k: v for k, v in kw.items() if v is not None}
        chat_completion = None
        if cache:
            chat_completion = _get_cache(kw)
        if chat_completion is None:
            try:
                async_response = await self._client.chat.completions.create(**kw)
            except openai.APIStatusError as e:
                raise status_error_map[e.status_code](e.message) from None
            if cache:
                _write_to_cache(kw, chat_completion)
        self.set_provider(async_response.model.split("@")[-1])  # type: ignore
        if message_content_only:
            content = async_response.choices[0].message.content
            if content:
                return content.strip(" ")
            return ""
        return async_response

    async def _generate(  # noqa: WPS234, WPS211
        self,
        user_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[Iterable[ChatCompletionMessageParam]] = None,
        *,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = 1024,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        stream: Optional[bool] = False,
        stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        # python client arguments
        message_content_only: bool = True,
        cache: bool = False,
        # passthrough arguments
        extra_headers: Optional[OpenAIHeaders] = None,
        extra_query: Optional[OpenAIQuery] = None,
        **kwargs,
    ) -> Union[AsyncGenerator[str, None], str]:  # noqa: DAR101, DAR201, DAR401
        contents = []
        if system_prompt:
            contents.append({"role": "system", "content": system_prompt})

        if user_prompt:
            contents.append({"role": "user", "content": user_prompt})
        elif messages:
            contents.extend(messages)
        else:
            raise UnifyError("You must provide either the user_prompt or messages!")
        query = Query(
            messages=contents,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            max_tokens=max_tokens,
            n=n,
            presence_penalty=presence_penalty,
            response_format=response_format,
            seed=seed,
            stop=stop,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=kwargs
        )
        if stream:
            return self._generate_stream(
                self._endpoint,
                **query.model_dump(),
                # stream
                stream_options=stream_options,
                # platform arguments
                use_custom_keys=use_custom_keys,
                tags=tags,
                # python client arguments
                message_content_only=message_content_only
            )
        return await self._generate_non_stream(
            self._endpoint,
            **query.model_dump(),
            # platform arguments
            use_custom_keys=use_custom_keys,
            tags=tags,
            # python client arguments
            message_content_only=message_content_only,
            cache=cache
        )
