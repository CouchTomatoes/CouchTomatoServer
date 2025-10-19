using Microsoft.Extensions.Options;

namespace CouchTomato.Core.Config;

public class ConfigService
{
    private readonly AppSettings _settings;
    public ConfigService(IOptions<AppSettings> settings)
    {
        _settings = settings.Value;
    }

    public AppSettings Get() => _settings;
}
