"team peggle specific commands"

from util import hook, http

def format_server(server):
	return "\x02%-16s\x02 steam://connect/%s" % (server.get('name')[0:16], server.get('host'))

@hook.command('server', autohelp=False)
@hook.command(autohelp=False)
def servers(inp, chan='', nick='', reply=None):
	servers = http.get_json('http://teampeggle.com/servers.json')

	if inp:
		server_id = int(inp) - 1
	
		if server_id >= 0 and server_id < len(servers):
			server = servers[server_id]

			return format_server(server)
		else:
			return 'No server found'

	for server in servers:
		reply(format_server(server))