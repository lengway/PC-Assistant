"""LLM-backed command parser.

Goal: convert free-form user text into a list of command dicts, then
into our Command objects. If LLM fails or no API key is configured,
fallback to the rule-based parser.
"""

import json
import os
import re
from typing import List, Union

import requests

from core.desktop import Command, parse_command
from dekstop_ops import get_desktop_items

API_KEY = os.environ.get("AI_API_KEY", "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")
API_BASE = os.environ.get("AI_API_BASE", "https://openrouter.ai/api/v1")
MODEL_NAME = os.environ.get("AI_MODEL", "allenai/molmo-2-8b:free")
OR_REFERER = os.environ.get("AI_HTTP_REFERER")
OR_TITLE = os.environ.get("AI_HTTP_TITLE")


def _desktop_inventory() -> str:
	items = get_desktop_items()
	if not items:
		return "Desktop items: []"
	names = sorted({p.name for p in items.values()})
	return "Desktop items: " + ", ".join(names)


def _build_prompt(user_text: str) -> str:
	return (
		"You are a command planner for a Windows desktop assistant. "
		"Produce ONLY JSON array of steps with no extra text. "
		"Allowed actions: open, rename, delete, create, get, help, exit. "
		"For create use args: kind ('file'|'folder'), name, ext (for files). "
		"For delete use args: target, confirm (true/false). "
		"For rename use args: old, new. "
		"For open/get use args: target/filter. "
		"If the request is unclear, return an empty array []. "
		f"User request: {user_text} "
		f"Context: {_desktop_inventory()}"
	)


def _extract_json(text: str) -> Union[List[dict], None]:
	try:
		return json.loads(text)
	except json.JSONDecodeError:
		pass

	match = re.search(r"\[(.|\n|\r)*\]", text)
	if match:
		try:
			return json.loads(match.group(0))
		except json.JSONDecodeError:
			return None
	return None


def _call_llm(text: str) -> Union[List[Command], str]:
	if not API_KEY:
		return "Пустой ключ API. Установите AI_API_KEY"

	payload = {
		"model": MODEL_NAME,
		"messages": [
			{"role": "system", "content": "You output only JSON arrays of steps."},
			{"role": "user", "content": _build_prompt(text)},
		],
		"temperature": 0.2,
	}

	headers = {
		"Authorization": f"Bearer {API_KEY}",
		"Content-Type": "application/json",
	}
	if OR_REFERER:
		headers["HTTP-Referer"] = OR_REFERER
	if OR_TITLE:
		headers["X-Title"] = OR_TITLE

	url = API_BASE.rstrip("/") + "/chat/completions"

	try:
		resp = requests.post(url, headers=headers, json=payload, timeout=30)
	except requests.RequestException as exc:
		return f"Ошибка сети при обращении к LLM: {exc}"

	if resp.status_code != 200:
		return f"LLM ответил ошибкой: {resp.status_code} {resp.text}"

	data = resp.json()
	content = (
		data.get("choices", [{}])[0]
		.get("message", {})
		.get("content", "")
	)

	steps_json = _extract_json(content)
	if steps_json is None:
		return "Не удалось разобрать ответ LLM"

	commands: List[Command] = []
	for step in steps_json:
		if not isinstance(step, dict):
			continue
		action = step.get("action", "")
		args = step.get("args", {}) if isinstance(step.get("args", {}), dict) else {}
		commands.append(Command(action, args))

	if not commands:
		return "LLM не вернул шаги"

	return commands


def parse_with_llm(text: str) -> Union[List[Command], str]:
	"""Convert free-form text into a list of Commands via LLM or fallback parser."""
	if not text.strip():
		return "Пустая команда"

	if API_KEY:
		llm_result = _call_llm(text)
		if isinstance(llm_result, list):
			return llm_result
		# No fallback when LLM is expected; surface the LLM error directly.
		return f"LLM ошибка: {llm_result}"

	# No API key: direct fallback, but signal that LLM is disabled
	parsed = parse_command(text)
	if isinstance(parsed, str):
		return f"LLM отключена (нет AI_API_KEY). {parsed}"
	return [parsed]
