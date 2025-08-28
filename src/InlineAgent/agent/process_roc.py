import copy
import inspect
import json
from typing import Any, Callable, Dict, Union
from termcolor import colored

from InlineAgent.constants import TraceColor


class ProcessROC:
    @staticmethod
    async def process_roc(
        inlineSessionState: Dict, roc_event: Dict, tool_map: Dict[str, Callable]
    ):
        # Validaciones iniciales
        if "returnControlInvocationResults" in inlineSessionState:
            raise ValueError(
                "returnControlInvocationResults key is not supported in sessionState"
            )

        if "invocationId" in inlineSessionState:
            raise ValueError("invocationId key is not supported in sessionState")

        inlineSessionState = copy.deepcopy(inlineSessionState)
        inlineSessionState = {"returnControlInvocationResults": []}
        inlineSessionState["invocationId"] = roc_event["invocationId"]

        for invocationInput in roc_event["invocationInputs"]:
            # Estructura Tagged Union
            if "apiInvocationInput" in invocationInput:
                raise ValueError(
                    "apiInvocationInput is not supported in returnControlInvocationResults"
                )

            actionInvocationType = invocationInput["functionInvocationInput"][
                "actionInvocationType"
            ]
            functionInvocationInput = invocationInput["functionInvocationInput"]
            actionGroup = functionInvocationInput["actionGroup"]

            # ✅ Procesamos parámetros con manejo robusto de arrays no JSON
            parameters = dict()
            for param in functionInvocationInput["parameters"]:
                if param["type"] == "array":
                    try:
                        # Intentamos parsear como JSON válido
                        result = json.loads(param["value"])
                    except json.JSONDecodeError:
                        # Si no es JSON válido, lo convertimos manualmente
                        clean_value = param["value"].strip("[] ")
                        if clean_value:
                            result = [
                                item.strip().strip('"').strip("'")
                                for item in clean_value.split(",")
                            ]
                        else:
                            result = []
                    parameters[param["name"]] = result

                elif param["type"] == "string":
                    parameters[param["name"]] = param["value"]

                elif param["type"] in ["number", "integer"]:
                    try:
                        parameters[param["name"]] = int(param["value"])
                    except ValueError:
                        raise ValueError(
                            f"Invalid integer value for {param['name']}: {param['value']}"
                        )

                elif param["type"] == "boolean":
                    parameters[param["name"]] = str(param["value"]).lower() in [
                        "true",
                        "1",
                        "yes",
                    ]

            # ✅ Invocación de herramientas según tipo de acción
            if actionInvocationType in ["RESULT", "USER_CONFIRMATION_AND_RESULT"]:
                tool_to_invoke: Callable = None
                if functionInvocationInput["function"] in tool_map:
                    tool_to_invoke = tool_map[functionInvocationInput["function"]]

                if not tool_to_invoke:
                    raise ValueError(
                        f"Function {functionInvocationInput['function']} not found in tools or tools class"
                    )

                if actionInvocationType == "USER_CONFIRMATION_AND_RESULT":
                    await ProcessROC.process_user_confirmation(
                        sessionState=inlineSessionState,
                        tool_to_invoke=tool_to_invoke,
                        functionInvocationInput=functionInvocationInput,
                        include_result=True,
                        parameters=parameters,
                    )
                else:
                    inlineSessionState["returnControlInvocationResults"].append(
                        {
                            "functionResult": await ProcessROC.invoke_roc_function(
                                functionInvocationInput=functionInvocationInput,
                                tool_to_invoke=tool_to_invoke,
                                parameters=parameters,
                                confirm=None,
                            )
                        }
                    )

            elif actionInvocationType == "USER_CONFIRMATION":
                tool_to_invoke = functionInvocationInput["function"]
                await ProcessROC.process_user_confirmation(
                    sessionState=inlineSessionState,
                    tool_to_invoke=tool_to_invoke,
                    functionInvocationInput=functionInvocationInput,
                    include_result=False,
                    parameters=parameters,
                )

        inlineSessionState.update(inlineSessionState)

        return inlineSessionState

    @staticmethod
    async def process_user_confirmation(
        sessionState: Dict,
        functionInvocationInput: Dict,
        include_result: bool,
        parameters: Dict,
        tool_to_invoke: Union[str, Callable] = None,
    ):
        while True:
            tool_name = (
                tool_to_invoke.__name__ if isinstance(tool_to_invoke, Callable) else tool_to_invoke
            )
            confirmation_message = f"Do you want to proceed with {tool_name} with parameters : {json.dumps(parameters)}?"
            response = input(f"{confirmation_message} (y/n): ").lower()
            if response in ["y", "yes"]:
                if include_result:
                    sessionState["returnControlInvocationResults"].append(
                        {
                            "functionResult": await ProcessROC.invoke_roc_function(
                                functionInvocationInput=functionInvocationInput,
                                tool_to_invoke=tool_to_invoke,
                                confirm="CONFIRM",
                                parameters=parameters,
                            )
                        }
                    )
                else:
                    sessionState["returnControlInvocationResults"].append(
                        {
                            "functionResult": {
                                "actionGroup": functionInvocationInput["actionGroup"],
                                "agentId": functionInvocationInput["agentId"],
                                "function": functionInvocationInput["function"],
                                "confirmationState": "CONFIRM",
                            }
                        }
                    )
                break
            elif response in ["n", "no"]:
                if include_result:
                    sessionState["returnControlInvocationResults"].append(
                        {
                            "functionResult": {
                                "actionGroup": functionInvocationInput["actionGroup"],
                                "agentId": functionInvocationInput["agentId"],
                                "function": functionInvocationInput["function"],
                                "responseBody": {
                                    "TEXT": {
                                        "body": "Access Denied to this function. Do not try again."
                                    }
                                },
                                "confirmationState": "DENY",
                            }
                        }
                    )
                else:
                    sessionState["returnControlInvocationResults"].append(
                        {
                            "functionResult": {
                                "actionGroup": functionInvocationInput["actionGroup"],
                                "agentId": functionInvocationInput["agentId"],
                                "function": functionInvocationInput["function"],
                                "confirmationState": "DENY",
                            }
                        }
                    )
                break
            else:
                print("Please enter 'y' for yes or 'n' for no.")

    @staticmethod
    async def invoke_roc_function(
        functionInvocationInput: Dict,
        parameters: Dict = dict(),
        confirm: str = None,
        tool_to_invoke: Callable = None,
    ) -> Dict:
        functionResult = dict

        try:
            if inspect.iscoroutinefunction(tool_to_invoke):
                result = await tool_to_invoke(**parameters)
            else:
                result = tool_to_invoke(**parameters)

            print(
                colored(
                    f"Tool output: {result}",
                    TraceColor.invocation_input,
                )
            )

            functionResult = {
                "actionGroup": functionInvocationInput["actionGroup"],
                "agentId": functionInvocationInput["agentId"],
                "function": functionInvocationInput["function"],
                "responseBody": {"TEXT": {"body": result}},
            }
        except Exception as e:
            functionResult = {
                "actionGroup": functionInvocationInput["actionGroup"],
                "agentId": functionInvocationInput["agentId"],
                "function": functionInvocationInput["function"],
                "responseBody": {"TEXT": {"body": str(e)}},
                "responseState": "FAILURE",
            }

        if confirm:
            if confirm == "CONFIRM":
                functionResult["confirmationState"] = confirm
                return functionResult
            else:
                raise ValueError("Only CONFIRM is a valid value")
        else:
            return functionResult
