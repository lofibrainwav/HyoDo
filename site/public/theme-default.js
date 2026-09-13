try {
	if (!localStorage.getItem('starlight-theme')) {
		localStorage.setItem('starlight-theme', 'dark');
	}
} catch {
	// Storage may be unavailable; Starlight can still render its theme selector.
}
