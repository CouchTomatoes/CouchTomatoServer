using AutoMapper;
using CouchTomato.Core.DTOs;
using CouchTomato.Data.Entities;

namespace CouchTomato.Core.Mapping;

public class MappingProfile : Profile
{
    public MappingProfile()
    {
        CreateMap<Movie, MovieDto>().ReverseMap();
    }
}
