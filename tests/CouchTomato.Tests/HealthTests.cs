using Xunit;
using CouchTomato.Core.Config;

namespace CouchTomato.Tests;

public class HealthTests
{
    [Fact]
    public void AppSettings_Defaults_AreValid()
    {
        var cfg = new AppSettings();
        Assert.Equal("CouchTomatoServer", cfg.ApplicationName);
        Assert.StartsWith("0.", cfg.Version);
    }
}
